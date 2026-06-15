import anthropic
import config  # ensures dotenv is loaded and API key is in environment

SYSTEM_PROMPT = (
    "Ты — личный второй мозг пользователя. Твоя роль: быть умным, заботливым помощником, ментором и советником. "
    "Ты помогаешь организовать мысли, даёшь практические советы, поддерживаешь в трудные моменты и мотивируешь достигать целей. "
    "Отвечай на русском языке. Будь тёплым, но конкретным. Не давай пустых советов — только практические шаги. "
    "Если пользователь в стрессе или устал — сначала поддержи эмоционально, потом предложи конкретные шаги."
)

STRESS_KEYWORDS = [
    "устал", "усталость", "стресс", "тревога", "тревожно", "плохо", "всё плохо",
    "ничего не получается", "не могу", "помоги", "паника", "страшно", "грустно",
    "грусть", "депрессия", "сложно", "тяжело", "не знаю что делать",
]

MODEL = "claude-3-5-haiku-20241022"


def _is_stressed(message: str) -> bool:
    lowered = message.lower()
    return any(kw in lowered for kw in STRESS_KEYWORDS)


async def get_ai_response(user_id: int, message: str, db) -> str:
    history = await db.get_conversation_history(user_id)

    system_prompt = SYSTEM_PROMPT
    if _is_stressed(message):
        system_prompt = (
            "ВАЖНО: Пользователь сейчас испытывает стресс или эмоциональные трудности. "
            "Сначала обязательно поддержи его эмоционально, прояви сочувствие и понимание. "
            "Только после этого предложи конкретные практические шаги.\n\n" + system_prompt
        )

    messages = list(history)
    messages.append({"role": "user", "content": message})

    client = anthropic.AsyncAnthropic()
    response = await client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system_prompt,
        messages=messages,
    )

    reply = response.content[0].text

    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": reply})

    if len(history) > 20:
        history = history[-20:]

    await db.save_conversation_history(user_id, history)

    return reply
