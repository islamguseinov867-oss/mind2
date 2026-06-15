import logging
from telegram import Update
from telegram.ext import ContextTypes
from services.ai import get_ai_response, detect_stress, get_support_message
import database

logger = logging.getLogger(__name__)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular text messages - route to AI."""
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
            msg = "😔 Превышена квота ИИ (Gemini). Попробуй чуть позже или проверь лимиты ключа."
        elif "API_KEY" in err or "API key" in err or "401" in err or "403" in err:
            msg = "🔑 Проблема с ключом Gemini — проверь GEMINI_API_KEY."
        else:
            msg = "😔 Извини, произошла ошибка при обработке сообщения. Попробуй ещё раз."
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
