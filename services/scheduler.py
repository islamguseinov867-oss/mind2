import logging
from datetime import datetime, time
from telegram.ext import Application
from config import MOTIVATION_HOUR, MOTIVATION_MINUTE
import database

logger = logging.getLogger(__name__)


async def _send_reminder(context):
    data = context.job.data
    try:
        await context.bot.send_message(
            chat_id=data["user_id"],
            text=f"⏰ *Напоминание!*\n\n{data['text']}",
            parse_mode="Markdown"
        )
        await database.mark_reminder_sent(data["reminder_id"])
    except Exception as e:
        logger.error(f"Failed to send reminder {data.get('reminder_id')}: {e}")


async def schedule_reminder(application: Application, reminder_id, user_id, text, remind_at):
    """Schedule a one-off reminder via the job queue."""
    delay = (remind_at - datetime.now()).total_seconds()
    if delay < 1:
        delay = 1
    application.job_queue.run_once(
        _send_reminder,
        when=delay,
        data={"reminder_id": reminder_id, "user_id": user_id, "text": text},
        name=f"reminder_{reminder_id}",
    )
    logger.info(f"Reminder {reminder_id} scheduled in {int(delay)}s.")


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
                    chat_id=user["user_id"],
                    text=message,
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Motivation send failed for {user['user_id']}: {e}")
    except Exception as e:
        logger.error(f"Motivation generation failed: {e}")


async def setup_daily_motivation(application: Application):
    application.job_queue.run_daily(
        send_daily_motivation,
        time=time(hour=MOTIVATION_HOUR, minute=MOTIVATION_MINUTE),
        name="daily_motivation",
    )
    logger.info("Daily motivation scheduled.")


async def check_and_reschedule_pending_reminders(application: Application, db):
    """On startup, re-schedule all reminders that haven't been sent yet."""
    rows = await database.get_all_unsent_reminders()
    count = 0
    for r in rows:
        try:
            remind_at = datetime.fromisoformat(r["remind_at"])
        except (ValueError, TypeError):
            continue
        await schedule_reminder(application, r["id"], r["user_id"], r["text"], remind_at)
        count += 1
    if count:
        logger.info(f"Rescheduled {count} pending reminder(s).")
