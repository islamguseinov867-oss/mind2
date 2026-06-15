# 🚀 Запуск бота 24/7 без компьютера (только браузер)

Бот будет работать в облаке бесплатно, на серверах GitHub.
Ни Python, ни Git, ни терминал — НЕ нужны. Только браузер.

## Шаг 1. Добавь 2 ключа в GitHub (это могу сделать только ты)

1. Открой репозиторий: **https://github.com/islamguseinov867-oss/mind2**
2. Сверху нажми **Settings** (Настройки)
3. Слева: **Secrets and variables → Actions**
4. Нажми зелёную кнопку **New repository secret**

Добавь **первый** ключ:
- **Name:** `TELEGRAM_BOT_TOKEN`
- **Secret:** *(вставь токен от @BotFather)*
- Нажми **Add secret**

Добавь **второй** ключ (снова New repository secret):
- **Name:** `GEMINI_API_KEY`
- **Secret:** *(вставь ключ с aistudio.google.com/apikey)*
- Нажми **Add secret**

> 🔑 Свои ключи я отправил тебе отдельным сообщением в чат — просто скопируй их в эти поля.

## Шаг 2. Запусти бота

1. Вверху репозитория нажми вкладку **Actions**
2. Если попросит — нажми **"I understand my workflows, enable them"**
3. Слева выбери **Run Telegram Bot**
4. Справа нажми **Run workflow → Run workflow**

Готово! Через минуту бот оживёт. Открой его в Telegram и напиши `/start`.

> Бот перезапускается автоматически каждые 5 часов (ограничение бесплатного GitHub).
> Он будет работать постоянно, пока включён workflow.

---

## Альтернатива: Render.com (работает без перезапусков)

1. Зайди на **https://render.com** через GitHub-аккаунт
2. **New → Blueprint**, выбери репозиторий `mind2`
3. Render сам найдёт `render.yaml`
4. Впиши те же 2 ключа (`TELEGRAM_BOT_TOKEN`, `GEMINI_API_KEY`)
5. **Apply** — бот запущен 24/7
