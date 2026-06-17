import re
import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from services.ai import get_ai_response, detect_stress, get_support_message
import database

logger = logging.getLogger(__name__)

# Паттерны для определения намерения поставить напоминание в свободной речи
_REMIND_PATTERNS = [
    (r"через\s+(\d+)\s+минут[уыа]?", "minutes"),
    (r"через\s+(\d+)\s+мин\b", "minutes"),
    (r"через\s+(\d+)\s+час[аов]?", "hours"),
    (r"через\s+(\d+)\s+ч\b", "hours"),
    (r"через\s+(\d+)\s+дней", "days"),
    (r"через\s+(\d+)\s+дня", "days"),
    (r"через\s+(\d+)\s+день", "days"),
]

_REMIND_TRIGGERS = [
    "напомни", "напоминание", "скинь", "пришли", "отправь", "скажи", "remind"
]


def _try_parse_reminder(text: str):
    """
    Возвращает (timedelta, reminder_text) если текст похож на запрос напоминания,
    иначе (None, None).
    """
    lower = text.lower()
    has_trigger = any(t in lower for t in _REMIND_TRIGGERS)
    if not has_trigger:
        return None, None

    for pattern, unit in _REMIND_PATTERNS:
        match = re.search(pattern, lower)
        if match:
            value = int(match.group(1))
            if unit == "minutes":
                delta = timedelta(minutes=value)
            elif unit == "hours":
                delta = timedelta(hours=value)
            else:
                delta = timedelta(days=value)
            # Берём оставшийся текст после временного выражения как описание
            remaining = text[match.end():].strip().strip(".,!?")
            if not remaining:
                remaining = text[:match.start()].strip().strip(".,!?")
            if not remaining:
                remaining = "Напоминание"
            return delta, remaining

    return None, None


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular text messages - route to AI or reminder."""
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    text = update.message.text

    await database.upsert_user(
        user.id,
        user.username or "",
        user.first_name or "",
        user.last_name or ""
    )

    # Проверяем — может это запрос на напоминание в свободной форме?
    delta, reminder_text = _try_parse_reminder(text)
    if delta is not None:
        from services import scheduler as scheduler_service
        remind_at = datetime.now() + delta
        db = context.application.bot_data.get("db")
        if db:
            reminder_id = await db.add_reminder(user.id, reminder_text, remind_at)
            if reminder_id != -1:
                await scheduler_service.schedule_reminder(
                    context.application, reminder_id, user.id, reminder_text, remind_at
                )
                total_s = int(delta.total_seconds())
                if total_s < 3600:
                    time_str = f"через {total_s // 60} мин."
                elif total_s < 86400:
                    time_str = f"через {total_s // 3600} ч."
                else:
                    time_str = f"через {total_s // 86400} д."
                await update.message.reply_text(
                    f"⏰ Понял! Напоминание установлено.\n\n"
                    f"📋 {reminder_text}\n"
                    f"🕐 {time_str} ({remind_at.strftime('%H:%M')})"
                )
                return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        if detect_stress(text) and len(text.split()) < 10:
            response = await get_support_message(text)
        else:
            response = await get_ai_response(user.id, text)

        await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"AI response error: {e}")
        err = str(e)
        if "RESOURCE_EXHAUSTED" in err or "429" in err or "quota" in err.lower():
            msg = "😔 Превышена квота ИИ (Gemini). Попробуй чуть позже."
        elif "API_KEY" in err or "API key" in err or "401" in err or "403" in err:
            msg = "🔑 Проблема с ключом Gemini — проверь GEMINI_API_KEY."
        else:
            msg = "😔 Извини, произошла ошибка. Попробуй ещё раз."
        await update.message.reply_text(msg)


async def motivation_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send motivation on demand."""
    from services.ai import get_motivation

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        motivation = await get_motivation()
        await update.message.reply_text(f"💪 *Мотивация для тебя:*\n\n{motivation}", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Motivation error: {e}")
        await update.message.reply_text("😔 Не удалось получить мотивацию. Попробуй позже.")
