# Mind2 — Личный Второй Мозг (Telegram Bot)

Telegram-бот на Python, который выступает в роли личного второго мозга: умный советник, органайзер заметок и задач, трекер целей, напоминания и ежедневная мотивация — всё в одном чате.

## Возможности

- **ИИ-чат** — диалог с Claude (Anthropic), контекст сохраняется между сообщениями
- **Заметки** — сохранение произвольных заметок командой `/note`
- **Задачи** — todo-список с возможностью отмечать выполненные
- **Напоминания** — установка напоминаний на русском языке (`через 30 минут`, `через 2 часа`, `через 1 день`)
- **Цели** — добавление и отслеживание целей со статусами (активная / выполнена / пауза)
- **Мотивация** — ежедневное мотивационное сообщение утром + команда `/motivation`
- **Поддержка** — бот определяет стресс по ключевым словам и отвечает с особой заботой

## Требования

- Python 3.10+
- Аккаунт Telegram и токен бота (через [@BotFather](https://t.me/BotFather))
- API-ключ Anthropic (https://console.anthropic.com)

## Установка и запуск

### 1. Клонируй репозиторий

```bash
git clone <repo-url>
cd mind2
```

### 2. Создай виртуальное окружение

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

### 3. Установи зависимости

```bash
pip install -r requirements.txt
```

### 4. Настрой переменные окружения

Скопируй `.env.example` в `.env` и заполни значения:

```bash
cp .env.example .env
```

Отредактируй `.env`:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
DATABASE_PATH=mind2.db
MOTIVATION_HOUR=9
MOTIVATION_MINUTE=0
```

| Переменная | Описание |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Токен бота от @BotFather |
| `ANTHROPIC_API_KEY` | Ключ API Anthropic Claude |
| `DATABASE_PATH` | Путь к файлу базы данных SQLite |
| `MOTIVATION_HOUR` | Час отправки ежедневной мотивации (UTC, 0-23) |
| `MOTIVATION_MINUTE` | Минута отправки ежедневной мотивации (0-59) |

### 5. Запусти бота

```bash
python bot.py
```

## Команды бота

| Команда | Описание |
|---|---|
| `/start` | Приветствие и список возможностей |
| `/help` | Справка по командам |
| `/note <текст>` | Сохранить заметку |
| `/note задача: <текст>` | Добавить задачу |
| `/notes` | Показать все заметки |
| `/tasks` | Показать задачи с кнопками выполнения |
| `/remind через 30 минут <текст>` | Установить напоминание |
| `/goals` | Показать цели |
| `/addgoal Название - Описание` | Добавить цель |
| `/motivation` | Получить мотивацию прямо сейчас |

## Структура проекта

```
mind2/
├── bot.py              # Точка входа
├── config.py           # Настройки из переменных окружения
├── database.py         # Слой работы с SQLite (aiosqlite)
├── handlers/
│   ├── __init__.py
│   ├── chat.py         # /start, /help, /motivation, ИИ-чат
│   ├── reminders.py    # /remind
│   ├── notes.py        # /note, /notes, /tasks
│   └── goals.py        # /goals, /addgoal
├── services/
│   ├── __init__.py
│   ├── ai.py           # Интеграция с Claude API
│   └── scheduler.py    # Планировщик напоминаний и мотивации
├── requirements.txt
├── .env.example
└── README.md
```

## База данных

SQLite-файл создаётся автоматически при первом запуске. Таблицы:

- **users** — пользователи и история диалога
- **notes** — заметки и задачи
- **reminders** — напоминания
- **goals** — цели пользователя
