import logging
import datetime
from telegram.ext import ContextTypes
import config
from services import ai as ai_service

logger = logging.getLogger(__name__)


async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    data = context.job.data
    user_id = data["user_id"]
    text = data["text"]
    reminder_id = data["reminder_id"]

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"⏰ Напоминание: {text}",
        )
    except Exception as e:
        logger.error(f"Failed to send reminder {reminder_id} to user {user_id}: {e}")

    db = context.application.bot_data.get("db")
    if db:
        await db.mark_reminder_sent(reminder_id)


async def schedule_reminder(application, reminder_id: int, user_id: int, text: str, remind_at: datetime.datetime):
    now = datetime.datetime.now()
    delta = (remind_at - now).total_seconds()
    if delta <= 0:
        logger.info(f"Reminder {reminder_id} is in the past, skipping.")
        return

    application.job_queue.run_once(
        send_reminder,
        when=delta,
        data={"user_id": user_id, "text": text, "reminder_id": reminder_id},
        name=f"reminder_{reminder_id}",
    )


async def send_daily_motivation(context: ContextTypes.DEFAULT_TYPE):
    db = context.application.bot_data.get("db")
    if not db:
        logger.error("No database found in bot_data for daily motivation.")
        return

    users = await db.get_all_users()
    motivation_prompt = (
        "Дай мне короткое мотивационное сообщение на день. "
        "Что-то вдохновляющее, практичное и тёплое. Не более 3-4 предложений."
    )

    for user in users:
        try:
            telegram_id = user["telegram_id"]
            message = await ai_service.get_ai_response(telegram_id, motivation_prompt, db)
            await context.bot.send_message(
                chat_id=telegram_id,
                text=f"🌅 Доброе утро! Ваша мотивация на день:\n\n{message}",
            )
        except Exception as e:
            logger.error(f"Failed to send daily motivation to user {user.get('telegram_id')}: {e}")


async def setup_daily_motivation(application):
    motivation_time = datetime.time(
        hour=config.MOTIVATION_HOUR,
        minute=config.MOTIVATION_MINUTE,
        tzinfo=None,
    )
    application.job_queue.run_daily(
        send_daily_motivation,
        time=motivation_time,
        name="daily_motivation",
    )


async def check_and_reschedule_pending_reminders(application, db):
    reminders = await db.get_pending_reminders(telegram_id=None)
    for reminder in reminders:
        try:
            remind_at = datetime.datetime.fromisoformat(reminder["remind_at"])
            await schedule_reminder(
                application,
                reminder_id=reminder["id"],
                user_id=reminder["telegram_id"],
                text=reminder["text"],
                remind_at=remind_at,
            )
        except Exception as e:
            logger.error(f"Failed to reschedule reminder {reminder.get('id')}: {e}")
