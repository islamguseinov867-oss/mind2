import json
import anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, MAX_HISTORY, STRESS_KEYWORDS
import database

client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Ты — «Второй Мозг», персональный ИИ-помощник, наставник и советник. Ты говоришь на русском языке.

Твоя роль:
- Быть поддерживающим, мотивирующим и практичным советником
- Помогать пользователю организовать мысли, задачи и цели
- Давать конкретные, actionable советы
- Помнить контекст разговора и использовать его
- Замечать эмоциональное состояние пользователя и реагировать с эмпатией

Стиль общения:
- Тёплый, но профессиональный
- Краткие, чёткие ответы (2-4 абзаца максимум, если не нужно больше)
- Используй структуру (списки, шаги) когда это помогает
- Не используй чрезмерных похвал типа "Отличный вопрос!"
- Будь честным и прямым

Если пользователь кажется уставшим, тревожным или в стрессе:
- Сначала прояви сочувствие и понимание
- Не давай сразу советов — сначала выслушай
- Предложи конкретную помощь после того, как поймёшь ситуацию

Ты можешь помочь с:
- Планированием и расстановкой приоритетов
- Принятием решений
- Личностным развитием
- Преодолением прокрастинации
- Управлением стрессом
- Анализом ситуаций и проблем"""


def detect_stress(text: str) -> bool:
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in STRESS_KEYWORDS)


async def get_ai_response(user_id: int, user_message: str) -> str:
    user = await database.get_user(user_id)

    history = []
    if user and user["conversation_history"]:
        try:
            history = json.loads(user["conversation_history"])
        except (json.JSONDecodeError, TypeError):
            history = []

    is_stressed = detect_stress(user_message)

    message_to_send = user_message
    if is_stressed:
        message_to_send = f"[Пользователь кажется в стрессе или расстроен]\n{user_message}"

    history.append({"role": "user", "content": message_to_send})

    if len(history) > MAX_HISTORY * 2:
        history = history[-(MAX_HISTORY * 2):]

    response = await client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=history
    )

    assistant_reply = response.content[0].text

    history.append({"role": "assistant", "content": assistant_reply})

    await database.update_conversation_history(user_id, json.dumps(history, ensure_ascii=False))

    return assistant_reply


async def get_motivation() -> str:
    response = await client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": "Дай мне короткое, мощное утреннее мотивационное послание на сегодня. Максимум 3-4 предложения. Что-то практичное и вдохновляющее, не банальное."
        }]
    )
    return response.content[0].text


async def get_support_message(user_message: str) -> str:
    response = await client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Пользователь написал: '{user_message}'. Он явно в стрессе или расстроен. Дай поддерживающий ответ с эмпатией, без лишних советов сразу. Сначала покажи что понимаешь его чувства."
        }]
    )
    return response.content[0].text
