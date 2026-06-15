import logging
from datetime import datetime, timezone
from telegram.ext import Application
from config import MOTIVATION_HOUR, MOTIVATION_MINUTE
import database

logger = logging.getLogger(__name__)


async def check_reminders(context):
    pending = await database.get_pending_reminders()
    for reminder in pending:
        try:
            await context.bot.send_message(
                chat_id=reminder["telegram_id"],
                text=f"⏰ *Напоминание!*\n\n{reminder['text']}",
                parse_mode="Markdown"
            )
            await database.mark_reminder_sent(reminder["id"])
        except Exception as e:
            logger.error(f"Failed to send reminder {reminder['id']}: {e}")


async def send_daily_motivation(context):
    from services.ai import get_motivation

    users = await database.get_all_users()
    if not users:
        return

    try:
        motivation_text = await get_motivation()
        message = f"🌅 *Доброе утро! Твоя утренняя мотивация:*\n\n{motivation_text}"
        for user in users:
            try:
                await context.bot.send_message(
                    chat_id=user["telegram_id"],
                    text=message,
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Motivation send failed for {user['telegram_id']}: {e}")
    except Exception as e:
        logger.error(f"Motivation generation failed: {e}")


async def setup_daily_motivation(application: Application):
    job_queue = application.job_queue
    job_queue.run_daily(
        send_daily_motivation,
        time=datetime.now(tz=timezone.utc).replace(
            hour=MOTIVATION_HOUR, minute=MOTIVATION_MINUTE, second=0, microsecond=0
        ).timetz(),
        name="daily_motivation"
    )
    # Check reminders every minute
    job_queue.run_repeating(check_reminders, interval=60, first=10, name="reminder_check")
    logger.info("Scheduler setup done.")


async def check_and_reschedule_pending_reminders(application: Application, db):
    # Reminders are handled by the repeating job above — nothing extra needed
    logger.info("Reminder scheduler active via repeating job.")
