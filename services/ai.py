import json
import asyncio
import logging
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, GEMINI_MODEL, MAX_HISTORY, STRESS_KEYWORDS
import database

logger = logging.getLogger(__name__)

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

# Модели по убыванию приоритета. Если основная упёрлась в лимит — пробуем следующую.
MODEL_CHAIN = list(dict.fromkeys(m for m in [GEMINI_MODEL, "gemini-2.5-flash-lite", "gemini-flash-latest"] if m))


def _make_config(system_instruction: str) -> types.GenerateContentConfig:
    return types.GenerateContentConfig(
        system_instruction=system_instruction,
        thinking_config=types.ThinkingConfig(thinking_budget=0),
    )


async def _generate(contents, system_instruction: str = SYSTEM_PROMPT) -> str:
    """Запрос к Gemini с ретраями и переключением моделей при лимите."""
    last_error = None
    for model in MODEL_CHAIN:
        for attempt in range(3):
            try:
                response = await asyncio.to_thread(
                    client.models.generate_content,
                    model=model,
                    contents=contents,
                    config=_make_config(system_instruction),
                )
                text = (response.text or "").strip()
                if text:
                    return text
                last_error = "empty response"
            except Exception as e:
                last_error = e
                err = str(e)
                if "RESOURCE_EXHAUSTED" in err or "429" in err or "quota" in err.lower():
                    await asyncio.sleep(2 * (attempt + 1))
                    continue
                if "API_KEY" in err or "API key" in err or "401" in err or "403" in err:
                    raise
                await asyncio.sleep(1)
        logger.warning(f"Model {model} failed: {last_error}")
    raise RuntimeError(f"All Gemini models failed: {last_error}")


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

    message_to_send = user_message
    if detect_stress(user_message):
        message_to_send = f"[Пользователь кажется в стрессе или расстроен]\n{user_message}"

    if len(history) > MAX_HISTORY * 2:
        history = history[-(MAX_HISTORY * 2):]

    contents = _build_contents(history, message_to_send)
    assistant_reply = await _generate(contents)

    history.append({"role": "user", "content": message_to_send})
    history.append({"role": "assistant", "content": assistant_reply})
    await database.update_conversation_history(user_id, json.dumps(history, ensure_ascii=False))

    return assistant_reply


async def get_motivation() -> str:
    return await _generate(
        "Дай мне короткое, мощное утреннее мотивационное послание на сегодня. Максимум 3-4 предложения. Что-то практичное и вдохновляющее, не банальное."
    )


async def get_support_message(user_message: str) -> str:
    return await _generate(
        f"Пользователь написал: '{user_message}'. Он явно в стрессе или расстроен. Дай поддерживающий ответ с эмпатией, без лишних советов сразу."
    )
