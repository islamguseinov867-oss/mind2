import logging

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import config
import database
from handlers.chat import handle_message, motivation_command
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

START_TEXT = """👋 Привет! Я твой *Второй Мозг* 🧠

Я помогу тебе:
• 💬 Советовать и отвечать на вопросы
• ⏰ Напоминать о важном
• 📝 Хранить заметки и задачи
• 🎯 Отслеживать цели
• 💪 Мотивировать каждый день

Просто напиши мне что угодно — я здесь!

/help — список всех команд"""

HELP_TEXT = """📋 *Команды:*

💬 *Чат*
Просто напиши — я отвечу как личный советник

📝 *Заметки*
/note текст — сохранить заметку
/notes — все заметки
/tasks — список задач

⏰ *Напоминания*
/remind через 30 минут позвонить маме
/remind через 2 часа проверить почту

🎯 *Цели*
/goals — мои цели
/addgoal название цели

💪 *Мотивация*
/motivation — получить мотивацию прямо сейчас"""


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await database.upsert_user(
        update.effective_user.id,
        update.effective_user.username or "",
        update.effective_user.first_name or "",
        update.effective_user.last_name or "",
    )
    await update.message.reply_text(START_TEXT, parse_mode="Markdown")


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def post_init(application: Application) -> None:
    db = database.Database()
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

    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("help", help_handler))
    application.add_handler(CommandHandler("note", note_handler))
    application.add_handler(CommandHandler("notes", notes_handler))
    application.add_handler(CommandHandler("tasks", tasks_handler))
    application.add_handler(CommandHandler("remind", remind_handler))
    application.add_handler(CommandHandler("goals", goals_handler))
    application.add_handler(CommandHandler("addgoal", addgoal_handler))
    application.add_handler(CommandHandler("motivation", motivation_command))

    application.add_handler(CallbackQueryHandler(task_done_callback, pattern=r"^task_done_"))
    application.add_handler(CallbackQueryHandler(goal_callback, pattern=r"^goal_"))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Starting bot polling...")
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
