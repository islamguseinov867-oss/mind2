import logging
from telegram import Update
from telegram.ext import ContextTypes
from services import ai as ai_service

logger = logging.getLogger(__name__)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = context.application.bot_data.get("db")
    if db:
        await db.get_or_create_user(user.id, user.username, user.first_name)

    welcome = (
        f"👋 Привет, {user.first_name}! Я твой личный второй мозг.\n\n"
        "Я помогу тебе:\n"
        "🤖 Отвечать на вопросы и давать советы\n"
        "📝 Записывать заметки и задачи\n"
        "⏰ Устанавливать напоминания\n"
        "🎯 Отслеживать цели\n"
        "💪 Мотивировать каждое утро\n\n"
        "Команды:\n"
        "/help — список команд\n"
        "/note <текст> — сохранить заметку\n"
        "/note задача: <текст> — добавить задачу\n"
        "/notes — все заметки\n"
        "/tasks — список задач\n"
        "/remind через 30 минут <текст> — установить напоминание\n"
        "/goals — мои цели\n"
        "/addgoal <название> - <описание> — добавить цель\n"
        "/motivation — получить мотивацию прямо сейчас\n\n"
        "Просто напиши мне что-нибудь — я всегда готов помочь! 🧠"
    )
    await update.message.reply_text(welcome)


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📖 *Список команд:*\n\n"
        "🤖 *ИИ Чат*\n"
        "Просто напиши любое сообщение — я отвечу как личный советник\n\n"
        "📝 *Заметки и задачи*\n"
        "/note <текст> — сохранить заметку\n"
        "/note задача: <текст> — добавить задачу\n"
        "/notes — все заметки\n"
        "/tasks — список задач с отметками\n\n"
        "⏰ *Напоминания*\n"
        "/remind через 30 минут позвонить маме\n"
        "/remind через 2 часа проверить почту\n"
        "/remind через 1 день купить продукты\n\n"
        "🎯 *Цели*\n"
        "/goals — мои цели\n"
        "/addgoal Выучить Python - Пройти курс до конца месяца\n\n"
        "💪 *Мотивация*\n"
        "/motivation — мотивационное сообщение прямо сейчас\n\n"
        "Каждое утро я буду присылать мотивацию автоматически! 🌅"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def motivation_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action("typing")
    db = context.application.bot_data.get("db")
    user = update.effective_user
    if db:
        await db.get_or_create_user(user.id, user.username, user.first_name)
    motivation_prompt = (
        "Дай мне короткое мотивационное сообщение на день. "
        "Что-то вдохновляющее, практичное и тёплое. Не более 3-4 предложений."
    )
    response = await ai_service.get_ai_response(user.id, motivation_prompt, db)
    await update.message.reply_text(f"💪 {response}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    db = context.application.bot_data.get("db")
    if db:
        await db.get_or_create_user(user.id, user.username, user.first_name)

    await update.message.chat.send_action("typing")

    try:
        response = await ai_service.get_ai_response(user.id, text, db)
    except Exception as e:
        logger.error(f"AI response error for user {user.id}: {e}")
        response = "Произошла ошибка при обработке запроса. Попробуй ещё раз."

    await update.message.reply_text(response)
