import re
import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from services import scheduler as scheduler_service

logger = logging.getLogger(__name__)

# Patterns: (regex, unit)
_PATTERNS = [
    (r"через\s+(\d+)\s+минут[уыа]?", "minutes"),
    (r"через\s+(\d+)\s+мин\b", "minutes"),
    (r"через\s+(\d+)\s+час[аов]?", "hours"),
    (r"через\s+(\d+)\s+ч\b", "hours"),
    (r"через\s+(\d+)\s+дней", "days"),
    (r"через\s+(\d+)\s+дня", "days"),
    (r"через\s+(\d+)\s+день", "days"),
    (r"через\s+(\d+)\s+д\b", "days"),
]


def _parse_time(text: str):
    """Returns (timedelta, reminder_text) or (None, original_text)."""
    lower = text.lower()
    for pattern, unit in _PATTERNS:
        match = re.search(pattern, lower)
        if match:
            value = int(match.group(1))
            if unit == "minutes":
                delta = timedelta(minutes=value)
            elif unit == "hours":
                delta = timedelta(hours=value)
            else:
                delta = timedelta(days=value)
            # Extract the reminder description (everything after the time expression)
            remaining = text[match.end():].strip()
            return delta, remaining
    return None, text


async def remind_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args_text = " ".join(context.args) if context.args else ""
    if not args_text:
        await update.message.reply_text(
            "⏰ Использование:\n"
            "/remind через 30 минут позвонить маме\n"
            "/remind через 2 часа проверить почту\n"
            "/remind через 1 день купить продукты"
        )
        return

    delta, reminder_text = _parse_time(args_text)

    if delta is None:
        await update.message.reply_text(
            "❌ Не смог понять время. Попробуй:\n"
            "/remind через 30 минут <что сделать>\n"
            "/remind через 2 часа <что сделать>\n"
            "/remind через 1 день <что сделать>"
        )
        return

    if not reminder_text:
        reminder_text = "Напоминание"

    remind_at = datetime.now() + delta
    user = update.effective_user
    db = context.application.bot_data.get("db")

    if not db:
        await update.message.reply_text("❌ Ошибка базы данных.")
        return

    await db.get_or_create_user(user.id, user.username, user.first_name)
    reminder_id = await db.add_reminder(user.id, reminder_text, remind_at)

    if reminder_id == -1:
        await update.message.reply_text("❌ Не удалось сохранить напоминание.")
        return

    await scheduler_service.schedule_reminder(
        context.application, reminder_id, user.id, reminder_text, remind_at
    )

    total_seconds = int(delta.total_seconds())
    if total_seconds < 3600:
        mins = total_seconds // 60
        time_str = f"через {mins} мин."
    elif total_seconds < 86400:
        hours = total_seconds // 3600
        time_str = f"через {hours} ч."
    else:
        days = total_seconds // 86400
        time_str = f"через {days} д."

    await update.message.reply_text(
        f"⏰ Напоминание установлено!\n\n"
        f"📋 {reminder_text}\n"
        f"🕐 {time_str} ({remind_at.strftime('%H:%M %d.%m.%Y')})"
    )
