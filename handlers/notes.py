import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def note_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args_text = " ".join(context.args) if context.args else ""
    if not args_text:
        await update.message.reply_text(
            "📝 Использование:\n"
            "/note <текст заметки>\n"
            "/note задача: <текст задачи>"
        )
        return

    user = update.effective_user
    db = context.application.bot_data.get("db")
    if not db:
        await update.message.reply_text("❌ Ошибка базы данных.")
        return

    await db.get_or_create_user(user.id, user.username, user.first_name)

    is_task = False
    content = args_text

    lower = args_text.lower()
    if lower.startswith("задача:") or lower.startswith("task:"):
        is_task = True
        content = args_text.split(":", 1)[1].strip()

    note_id = await db.add_note(user.id, content, is_task)

    if note_id == -1:
        await update.message.reply_text("❌ Не удалось сохранить.")
        return

    if is_task:
        await update.message.reply_text(f"✅ Задача добавлена:\n{content}")
    else:
        await update.message.reply_text(f"📝 Заметка сохранена:\n{content}")


async def notes_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = context.application.bot_data.get("db")
    if not db:
        await update.message.reply_text("❌ Ошибка базы данных.")
        return

    await db.get_or_create_user(user.id, user.username, user.first_name)
    notes = await db.get_notes(user.id)

    if not notes:
        await update.message.reply_text(
            "📭 У тебя пока нет заметок.\nДобавь первую: /note <текст>"
        )
        return

    lines = ["📝 *Твои заметки:*\n"]
    for i, note in enumerate(notes, 1):
        lines.append(f"{i}. {note['content']}")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def tasks_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = context.application.bot_data.get("db")
    if not db:
        await update.message.reply_text("❌ Ошибка базы данных.")
        return

    await db.get_or_create_user(user.id, user.username, user.first_name)
    tasks = await db.get_tasks(user.id)

    if not tasks:
        await update.message.reply_text(
            "📭 У тебя пока нет задач.\nДобавь: /note задача: <текст>"
        )
        return

    lines = ["✅ *Список задач:*\n"]
    keyboard = []

    for task in tasks:
        checkbox = "☑️" if task["is_done"] else "⬜"
        lines.append(f"{checkbox} {task['content']}")
        if not task["is_done"]:
            label = task["content"][:30]
            keyboard.append(
                [InlineKeyboardButton(f"✅ {label}", callback_data=f"task_done_{task['id']}")]
            )

    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    await update.message.reply_text(
        "\n".join(lines), parse_mode="Markdown", reply_markup=reply_markup
    )


async def task_done_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    task_id = int(query.data.replace("task_done_", ""))
    user = update.effective_user
    db = context.application.bot_data.get("db")

    if not db:
        await query.edit_message_text("❌ Ошибка базы данных.")
        return

    success = await db.mark_task_done(task_id, user.id)
    if success:
        await query.edit_message_text("✅ Задача выполнена! Отличная работа! 🎉")
    else:
        await query.edit_message_text("❌ Не удалось обновить задачу.")
