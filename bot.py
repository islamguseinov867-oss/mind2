import asyncio
import logging

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

import config
import database
from handlers.chat import handle_message, help_handler, motivation_handler, start_handler
from handlers.goals import addgoal_handler, goal_callback, goals_handler
from handlers.notes import note_handler, notes_handler, task_done_callback, tasks_handler
from handlers.reminders import remind_handler
from services.scheduler import (
    check_and_reschedule_pending_reminders,
    setup_daily_motivation,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def post_init(application: Application) -> None:
    db = database.Database(config.DATABASE_PATH)
    await db.init_db()
    application.bot_data["db"] = db
    await setup_daily_motivation(application)
    await check_and_reschedule_pending_reminders(application, db)
    logger.info("Bot initialized successfully.")


def main() -> None:
    application = (
        Application.builder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # Command handlers
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("help", help_handler))
    application.add_handler(CommandHandler("note", note_handler))
    application.add_handler(CommandHandler("notes", notes_handler))
    application.add_handler(CommandHandler("tasks", tasks_handler))
    application.add_handler(CommandHandler("remind", remind_handler))
    application.add_handler(CommandHandler("goals", goals_handler))
    application.add_handler(CommandHandler("addgoal", addgoal_handler))
    application.add_handler(CommandHandler("motivation", motivation_handler))

    # Callback query handlers
    application.add_handler(CallbackQueryHandler(task_done_callback, pattern=r"^task_done_"))
    application.add_handler(CallbackQueryHandler(goal_callback, pattern=r"^goal_"))

    # General message handler (AI chat) — must be last
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Starting bot polling...")
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
