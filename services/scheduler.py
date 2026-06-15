import asyncio
import logging
from datetime import datetime
from telegram import Bot
from telegram.ext import Application
import database

logger = logging.getLogger(__name__)


async def check_reminders(context):
    """Check and send pending reminders."""
    pending = await database.get_pending_reminders()
    for reminder in pending:
        try:
            await context.bot.send_message(
                chat_id=reminder["user_id"],
                text=f"⏰ *Напоминание!*\n\n{reminder['text']}",
                parse_mode="Markdown"
            )
            await database.mark_reminder_sent(reminder["id"])
        except Exception as e:
            logger.error(f"Failed to send reminder {reminder['id']}: {e}")


async def send_daily_motivation(context):
    """Send daily motivation to all users."""
    from services.ai import get_motivation

    users = await database.get_all_users()
    if not users:
        return

    try:
        motivation_text = await get_motivation()
        message = f"🌅 *Доброе утро! Ваша утренняя доза мотивации:*\n\n{motivation_text}"

        for user in users:
            try:
                await context.bot.send_message(
                    chat_id=user["user_id"],
                    text=message,
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Failed to send motivation to user {user['user_id']}: {e}")
    except Exception as e:
        logger.error(f"Failed to generate motivation: {e}")
