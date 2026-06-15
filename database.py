import aiosqlite
import asyncio
from datetime import datetime
from config import DATABASE_PATH


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
        now = datetime.utcnow().isoformat()
        async with db.execute(
            "SELECT * FROM reminders WHERE is_sent = 0 AND remind_at <= ?",
            (now,)
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
