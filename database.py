import aiosqlite
import asyncio
import logging
from datetime import datetime
from config import DATABASE_PATH

logger = logging.getLogger(__name__)


async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                conversation_history TEXT DEFAULT '[]'
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                tags TEXT DEFAULT '',
                is_task INTEGER DEFAULT 0,
                is_done INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                remind_at TIMESTAMP NOT NULL,
                is_sent INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                status TEXT DEFAULT 'active',
                progress INTEGER DEFAULT 0,
                deadline TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        await db.commit()


# --- Users ---

async def upsert_user(user_id: int, username: str, first_name: str, last_name: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username=excluded.username,
                first_name=excluded.first_name,
                last_name=excluded.last_name
        """, (user_id, username, first_name, last_name))
        await db.commit()


async def get_user(user_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone()


async def get_all_users():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT user_id FROM users") as cursor:
            return await cursor.fetchall()


async def update_conversation_history(user_id: int, history_json: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE users SET conversation_history = ? WHERE user_id = ?",
            (history_json, user_id)
        )
        await db.commit()


# --- Notes ---

async def add_note(user_id: int, content: str, is_task: bool = False, tags: str = ""):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO notes (user_id, content, is_task, tags) VALUES (?, ?, ?, ?)",
            (user_id, content, 1 if is_task else 0, tags)
        )
        await db.commit()
        return cursor.lastrowid


async def get_notes(user_id: int, only_tasks: bool = False):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        if only_tasks:
            async with db.execute(
                "SELECT * FROM notes WHERE user_id = ? AND is_task = 1 ORDER BY created_at DESC",
                (user_id,)
            ) as cursor:
                return await cursor.fetchall()
        else:
            async with db.execute(
                "SELECT * FROM notes WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            ) as cursor:
                return await cursor.fetchall()


async def mark_task_done(note_id: int, user_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE notes SET is_done = 1 WHERE id = ? AND user_id = ?",
            (note_id, user_id)
        )
        await db.commit()


async def delete_note(note_id: int, user_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "DELETE FROM notes WHERE id = ? AND user_id = ?",
            (note_id, user_id)
        )
        await db.commit()


# --- Reminders ---

async def add_reminder(user_id: int, text: str, remind_at: datetime):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO reminders (user_id, text, remind_at) VALUES (?, ?, ?)",
            (user_id, text, remind_at.isoformat())
        )
        await db.commit()
        return cursor.lastrowid


async def get_pending_reminders():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        now = datetime.now().isoformat()
        async with db.execute(
            "SELECT * FROM reminders WHERE is_sent = 0 AND remind_at <= ?",
            (now,)
        ) as cursor:
            return await cursor.fetchall()


async def get_all_unsent_reminders():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM reminders WHERE is_sent = 0 ORDER BY remind_at ASC"
        ) as cursor:
            return await cursor.fetchall()


async def mark_reminder_sent(reminder_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE reminders SET is_sent = 1 WHERE id = ?",
            (reminder_id,)
        )
        await db.commit()


async def get_user_reminders(user_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM reminders WHERE user_id = ? AND is_sent = 0 ORDER BY remind_at ASC",
            (user_id,)
        ) as cursor:
            return await cursor.fetchall()


# --- Goals ---

async def add_goal(user_id: int, title: str, description: str = "", deadline: str = ""):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO goals (user_id, title, description, deadline) VALUES (?, ?, ?, ?)",
            (user_id, title, description, deadline)
        )
        await db.commit()
        return cursor.lastrowid


async def get_goals(user_id: int, status: str = None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        if status:
            async with db.execute(
                "SELECT * FROM goals WHERE user_id = ? AND status = ? ORDER BY created_at DESC",
                (user_id, status)
            ) as cursor:
                return await cursor.fetchall()
        else:
            async with db.execute(
                "SELECT * FROM goals WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            ) as cursor:
                return await cursor.fetchall()


async def update_goal_status(goal_id: int, user_id: int, status: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE goals SET status = ?, updated_at = ? WHERE id = ? AND user_id = ?",
            (status, datetime.utcnow().isoformat(), goal_id, user_id)
        )
        await db.commit()


async def update_goal_progress(goal_id: int, user_id: int, progress: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE goals SET progress = ?, updated_at = ? WHERE id = ? AND user_id = ?",
            (progress, datetime.utcnow().isoformat(), goal_id, user_id)
        )
        await db.commit()


async def delete_goal(goal_id: int, user_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "DELETE FROM goals WHERE id = ? AND user_id = ?",
            (goal_id, user_id)
        )
        await db.commit()


# --- Database class (used by handlers via bot_data["db"]) ---

class Database:
    """Object-oriented wrapper over the module-level functions above.
    Returns dicts (so handlers can use .get()) and never raises on writes."""

    def __init__(self, path: str = None):
        self.path = path or DATABASE_PATH

    async def init_db(self):
        await init_db()

    async def get_or_create_user(self, user_id, username=None, first_name=None, last_name=None):
        await upsert_user(user_id, username or "", first_name or "", last_name or "")

    async def add_note(self, user_id, content, is_task=False):
        try:
            return await add_note(user_id, content, is_task)
        except Exception as e:
            logger.error(f"add_note failed: {e}")
            return -1

    async def get_notes(self, user_id):
        return [dict(r) for r in await get_notes(user_id)]

    async def get_tasks(self, user_id):
        return [dict(r) for r in await get_notes(user_id, only_tasks=True)]

    async def mark_task_done(self, note_id, user_id):
        try:
            await mark_task_done(note_id, user_id)
            return True
        except Exception as e:
            logger.error(f"mark_task_done failed: {e}")
            return False

    async def get_goals(self, user_id):
        return [dict(r) for r in await get_goals(user_id)]

    async def add_goal(self, user_id, title, description=""):
        try:
            return await add_goal(user_id, title, description)
        except Exception as e:
            logger.error(f"add_goal failed: {e}")
            return -1

    async def update_goal_status(self, goal_id, user_id, status):
        try:
            await update_goal_status(goal_id, user_id, status)
            return True
        except Exception as e:
            logger.error(f"update_goal_status failed: {e}")
            return False

    async def add_reminder(self, user_id, text, remind_at):
        try:
            return await add_reminder(user_id, text, remind_at)
        except Exception as e:
            logger.error(f"add_reminder failed: {e}")
            return -1
