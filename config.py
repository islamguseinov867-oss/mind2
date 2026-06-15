import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
DATABASE_PATH = os.getenv("DATABASE_PATH", "mind2.db")
MOTIVATION_HOUR = int(os.getenv("MOTIVATION_HOUR", "9"))
MOTIVATION_MINUTE = int(os.getenv("MOTIVATION_MINUTE", "0"))

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY is not set")
