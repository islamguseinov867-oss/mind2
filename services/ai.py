import json
import asyncio
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, GEMINI_MODEL, MAX_HISTORY, STRESS_KEYWORDS
import database

client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """Ты — «Второй Мозг», персональный ИИ-помощник, наставник и советник. Ты говоришь на русском языке.

Твоя роль:
- Быть поддерживающим, мотивирующим и практичным советником
- Помогать пользователю организовать мысли, задачи и цели
- Давать конкретные, actionable советы
- Помнить контекст разговора и использовать его
- Замечать эмоциональное состояние пользователя и реагировать с эмпатией

Стиль общения:
- Тёплый, но профессиональный
- Краткие, чёткие ответы (2-4 абзаца максимум)
- Используй структуру (списки, шаги) когда это помогает
- Не используй чрезмерных похвал типа "Отличный вопрос!"
- Будь честным и прямым

Если пользователь кажется уставшим, тревожным или в стрессе:
- Сначала прояви сочувствие и понимание
- Не давай сразу советов — сначала выслушай
- Предложи конкретную помощь после того, как поймёшь ситуацию"""


def detect_stress(text: str) -> bool:
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in STRESS_KEYWORDS)


def _build_contents(history: list, user_message: str) -> list:
    contents = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))
    contents.append(types.Content(role="user", parts=[types.Part(text=user_message)]))
    return contents


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

    if len(history) > MAX_HISTORY * 2:
        history = history[-(MAX_HISTORY * 2):]

    contents = _build_contents(history, message_to_send)

    response = await asyncio.to_thread(
        client.models.generate_content,
        model=GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
    )
    assistant_reply = response.text

    history.append({"role": "user", "content": message_to_send})
    history.append({"role": "assistant", "content": assistant_reply})

    await database.update_conversation_history(user_id, json.dumps(history, ensure_ascii=False))

    return assistant_reply


async def get_motivation() -> str:
    response = await asyncio.to_thread(
        client.models.generate_content,
        model=GEMINI_MODEL,
        contents="Дай мне короткое, мощное утреннее мотивационное послание на сегодня. Максимум 3-4 предложения. Что-то практичное и вдохновляющее, не банальное.",
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
    )
    return response.text


async def get_support_message(user_message: str) -> str:
    response = await asyncio.to_thread(
        client.models.generate_content,
        model=GEMINI_MODEL,
        contents=f"Пользователь написал: '{user_message}'. Он явно в стрессе или расстроен. Дай поддерживающий ответ с эмпатией, без лишних советов сразу.",
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
    )
    return response.text
