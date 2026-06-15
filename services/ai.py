import json
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL, MAX_HISTORY, STRESS_KEYWORDS
import database

genai.configure(api_key=GEMINI_API_KEY)

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


def _build_gemini_history(history: list) -> list:
    gemini_history = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        gemini_history.append({"role": role, "parts": [msg["content"]]})
    return gemini_history


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

    # Keep history without current message for Gemini chat history
    if len(history) > MAX_HISTORY * 2:
        history = history[-(MAX_HISTORY * 2):]

    gemini_history = _build_gemini_history(history)

    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        system_instruction=SYSTEM_PROMPT
    )
    chat = model.start_chat(history=gemini_history)
    response = chat.send_message(message_to_send)
    assistant_reply = response.text

    history.append({"role": "user", "content": message_to_send})
    history.append({"role": "assistant", "content": assistant_reply})

    await database.update_conversation_history(user_id, json.dumps(history, ensure_ascii=False))

    return assistant_reply


async def get_motivation() -> str:
    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        system_instruction=SYSTEM_PROMPT
    )
    response = model.generate_content(
        "Дай мне короткое, мощное утреннее мотивационное послание на сегодня. Максимум 3-4 предложения. Что-то практичное и вдохновляющее, не банальное."
    )
    return response.text


async def get_support_message(user_message: str) -> str:
    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        system_instruction=SYSTEM_PROMPT
    )
    response = model.generate_content(
        f"Пользователь написал: '{user_message}'. Он явно в стрессе или расстроен. Дай поддерживающий ответ с эмпатией, без лишних советов сразу. Сначала покажи что понимаешь его чувства."
    )
    return response.text
