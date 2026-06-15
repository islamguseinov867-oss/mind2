import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

STATUS_EMOJI = {"active": "🎯", "done": "✅", "paused": "⏸️"}
STATUS_TEXT = {"active": "Активная", "done": "Выполнена", "paused": "На паузе"}


async def goals_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = context.application.bot_data.get("db")
    if not db:
        await update.message.reply_text("❌ Ошибка базы данных.")
        return

    await db.get_or_create_user(user.id, user.username, user.first_name)
    goals = await db.get_goals(user.id)

    if not goals:
        await update.message.reply_text(
            "🎯 У тебя пока нет целей.\n\n"
            "Добавь первую:\n"
            "/addgoal Название - Описание"
        )
        return

    lines = ["🎯 *Твои цели:*\n"]
    keyboard = []

    for goal in goals:
        emoji = STATUS_EMOJI.get(goal["status"], "🎯")
        status_label = STATUS_TEXT.get(goal["status"], goal["status"])
        lines.append(f"{emoji} *{goal['title']}*")
        if goal.get("description"):
            lines.append(f"   {goal['description']}")
        lines.append(f"   Статус: {status_label}\n")

        row = []
        if goal["status"] != "done":
            row.append(InlineKeyboardButton("✅ Выполнено", callback_data=f"goal_done_{goal['id']}"))
        if goal["status"] != "paused":
            row.append(InlineKeyboardButton("⏸️ Пауза", callback_data=f"goal_pause_{goal['id']}"))
        if goal["status"] != "active":
            row.append(InlineKeyboardButton("🎯 Активно", callback_data=f"goal_active_{goal['id']}"))
        if row:
            keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    await update.message.reply_text(
        "\n".join(lines), parse_mode="Markdown", reply_markup=reply_markup
    )


async def addgoal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args_text = " ".join(context.args) if context.args else ""
    if not args_text:
        await update.message.reply_text(
            "🎯 Использование:\n"
            "/addgoal Название - Описание\n\n"
            "Пример:\n"
            "/addgoal Выучить Python - Пройти курс до конца месяца"
        )
        return

    if " - " in args_text:
        title, description = args_text.split(" - ", 1)
        title = title.strip()
        description = description.strip()
    else:
        title = args_text.strip()
        description = ""

    user = update.effective_user
    db = context.application.bot_data.get("db")
    if not db:
        await update.message.reply_text("❌ Ошибка базы данных.")
        return

    await db.get_or_create_user(user.id, user.username, user.first_name)
    goal_id = await db.add_goal(user.id, title, description)

    if goal_id == -1:
        await update.message.reply_text("❌ Не удалось добавить цель.")
        return

    text = f"🎯 Цель добавлена!\n\n*{title}*"
    if description:
        text += f"\n{description}"
    await update.message.reply_text(text, parse_mode="Markdown")


async def goal_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user = update.effective_user
    db = context.application.bot_data.get("db")

    if not db:
        await query.edit_message_text("❌ Ошибка базы данных.")
        return

    if data.startswith("goal_done_"):
        goal_id = int(data.replace("goal_done_", ""))
        new_status = "done"
        msg = "✅ Цель выполнена! Поздравляю! 🎉"
    elif data.startswith("goal_pause_"):
        goal_id = int(data.replace("goal_pause_", ""))
        new_status = "paused"
        msg = "⏸️ Цель поставлена на паузу."
    elif data.startswith("goal_active_"):
        goal_id = int(data.replace("goal_active_", ""))
        new_status = "active"
        msg = "🎯 Цель снова активна! Вперёд!"
    else:
        return

    success = await db.update_goal_status(goal_id, user.id, new_status)
    if success:
        await query.edit_message_text(msg)
    else:
        await query.edit_message_text("❌ Не удалось обновить цель.")
