import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DATABASE_PATH = os.getenv("DATABASE_PATH", "mind2.db")

# Daily motivation time (hour, minute in UTC)
MOTIVATION_HOUR = int(os.getenv("MOTIVATION_HOUR", "7"))
MOTIVATION_MINUTE = int(os.getenv("MOTIVATION_MINUTE", "0"))

# Gemini model
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# Max conversation history per user
MAX_HISTORY = 10

# Stress detection keywords (Russian)
STRESS_KEYWORDS = [
    "устал", "устала", "стресс", "тревога", "тревожно", "плохо",
    "не могу", "не справляюсь", "помогите", "всё плохо", "всё пропало",
    "депрессия", "грустно", "грустить", "беспокоит", "паника", "страшно",
    "тяжело", "сложно", "не знаю что делать", "опустились руки",
    "нет сил", "выгорание", "перегрузка"
]
