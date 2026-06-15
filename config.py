import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
DATABASE_PATH = os.getenv("DATABASE_PATH", "mind2.db")

# Daily motivation time (hour, minute in UTC)
MOTIVATION_HOUR = int(os.getenv("MOTIVATION_HOUR", "7"))
MOTIVATION_MINUTE = int(os.getenv("MOTIVATION_MINUTE", "0"))

# Claude model
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-4-5")

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
