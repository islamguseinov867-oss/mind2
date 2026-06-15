import json
import aiosqlite
from datetime import datetime
from typing import Optional


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    conversation_history TEXT DEFAULT '[]',
                    created_at TEXT NOT NULL
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    is_task INTEGER NOT NULL DEFAULT 0,
                    is_done INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    remind_at TEXT NOT NULL,
                    is_sent INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            await db.commit()

    async def get_or_create_user(self, telegram_id: int, username: Optional[str], first_name: Optional[str]) -> dict:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
            now = datetime.now().isoformat()
            async with db.execute(
                "INSERT INTO users (telegram_id, username, first_name, conversation_history, created_at) VALUES (?, ?, ?, ?, ?)",
                (telegram_id, username, first_name, "[]", now),
            ) as cursor:
                user_id = cursor.lastrowid
            await db.commit()
            async with db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row)

    async def get_all_users(self) -> list:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users") as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def add_note(self, telegram_id: int, content: str, is_task: bool = False) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return -1
                user_id = row[0]
            now = datetime.now().isoformat()
            async with db.execute(
                "INSERT INTO notes (user_id, content, is_task, is_done, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, content, 1 if is_task else 0, 0, now),
            ) as cursor:
                note_id = cursor.lastrowid
            await db.commit()
            return note_id

    async def get_notes(self, telegram_id: int) -> list:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT n.* FROM notes n
                   JOIN users u ON n.user_id = u.id
                   WHERE u.telegram_id = ? AND n.is_task = 0
                   ORDER BY n.created_at DESC""",
                (telegram_id,),
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def get_tasks(self, telegram_id: int) -> list:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT n.* FROM notes n
                   JOIN users u ON n.user_id = u.id
                   WHERE u.telegram_id = ? AND n.is_task = 1
                   ORDER BY n.created_at DESC""",
                (telegram_id,),
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def mark_task_done(self, note_id: int, telegram_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                """UPDATE notes SET is_done = 1
                   WHERE id = ? AND user_id = (SELECT id FROM users WHERE telegram_id = ?)""",
                (note_id, telegram_id),
            ) as cursor:
                affected = cursor.rowcount
            await db.commit()
            return affected > 0

    async def add_reminder(self, telegram_id: int, text: str, remind_at: datetime) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return -1
                user_id = row[0]
            now = datetime.now().isoformat()
            async with db.execute(
                "INSERT INTO reminders (user_id, text, remind_at, is_sent, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, text, remind_at.isoformat(), 0, now),
            ) as cursor:
                reminder_id = cursor.lastrowid
            await db.commit()
            return reminder_id

    async def get_pending_reminders(self, telegram_id: Optional[int] = None) -> list:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if telegram_id is not None:
                async with db.execute(
                    """SELECT r.*, u.telegram_id as telegram_id FROM reminders r
                       JOIN users u ON r.user_id = u.id
                       WHERE u.telegram_id = ? AND r.is_sent = 0
                       ORDER BY r.remind_at""",
                    (telegram_id,),
                ) as cursor:
                    rows = await cursor.fetchall()
            else:
                async with db.execute(
                    """SELECT r.*, u.telegram_id as telegram_id FROM reminders r
                       JOIN users u ON r.user_id = u.id
                       WHERE r.is_sent = 0
                       ORDER BY r.remind_at"""
                ) as cursor:
                    rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def mark_reminder_sent(self, reminder_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE reminders SET is_sent = 1 WHERE id = ?", (reminder_id,))
            await db.commit()

    async def add_goal(self, telegram_id: int, title: str, description: Optional[str]) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return -1
                user_id = row[0]
            now = datetime.now().isoformat()
            async with db.execute(
                "INSERT INTO goals (user_id, title, description, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, title, description, "active", now, now),
            ) as cursor:
                goal_id = cursor.lastrowid
            await db.commit()
            return goal_id

    async def get_goals(self, telegram_id: int) -> list:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT g.* FROM goals g
                   JOIN users u ON g.user_id = u.id
                   WHERE u.telegram_id = ?
                   ORDER BY g.created_at DESC""",
                (telegram_id,),
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def update_goal_status(self, goal_id: int, telegram_id: int, status: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            now = datetime.now().isoformat()
            async with db.execute(
                """UPDATE goals SET status = ?, updated_at = ?
                   WHERE id = ? AND user_id = (SELECT id FROM users WHERE telegram_id = ?)""",
                (status, now, goal_id, telegram_id),
            ) as cursor:
                affected = cursor.rowcount
            await db.commit()
            return affected > 0

    async def get_conversation_history(self, telegram_id: int) -> list:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT conversation_history FROM users WHERE telegram_id = ?", (telegram_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return []
                return json.loads(row[0] or "[]")

    async def save_conversation_history(self, telegram_id: int, history: list):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET conversation_history = ? WHERE telegram_id = ?",
                (json.dumps(history, ensure_ascii=False), telegram_id),
            )
            await db.commit()
