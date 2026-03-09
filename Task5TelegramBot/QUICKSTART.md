# Быстрый старт

## 1. Настройка Python API

```bash
cd Task5
pip install -r requirements.txt
python api_secure.py
```

API должен запуститься на `http://localhost:8000`

## 2. Настройка переменных окружения

Установите переменные окружения:

**Windows (PowerShell):**
```powershell
$env:TELEGRAM_BOT_TOKEN="your_bot_token"
$env:TELEGRAM_BOT_USERNAME="your_bot_username"
```

**Linux/Mac:**
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_BOT_USERNAME="your_bot_username"
```

## 3. Запуск Java приложения

```bash
cd Task5TelegramBot
mvn spring-boot:run
```

## 4. Использование

Найдите бота в Telegram и отправьте:
- `/start` - приветствие
- `/help` - справка
- Любой вопрос о Star Wars

## Получение Telegram Bot Token

1. Найдите @BotFather в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Скопируйте полученный токен

