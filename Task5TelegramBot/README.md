# Task5 Telegram Bot

Telegram бот на Java (Spring Boot) для работы с защищенным RAG-сервисом из Task5.

## Описание

Этот проект представляет собой прокси-сервис на Java, который:
- Принимает сообщения от пользователей через Telegram
- Проксирует запросы к Python API серверу (Task5/api_secure.py)
- Возвращает ответы пользователям в Telegram

## Требования

- Java 17 или выше
- Maven 3.6+
- Python 3.8+ (для запуска Python API сервера)
- Telegram Bot Token (получить у @BotFather)

## Установка и настройка

### 1. Настройка Python API сервера

Сначала убедитесь, что Python API сервер настроен и может быть запущен:

```bash
cd Task5
pip install -r requirements.txt
# Убедитесь, что установлен fastapi и uvicorn
pip install fastapi uvicorn
```

### 2. Настройка переменных окружения

Создайте файл `.env` в корне проекта или установите переменные окружения:

```bash
# Telegram Bot
export TELEGRAM_BOT_TOKEN=your_telegram_bot_token
export TELEGRAM_BOT_USERNAME=your_bot_username

# Python API (опционально, по умолчанию http://localhost:8000)
export PYTHON_API_URL=http://localhost:8000
export PYTHON_API_TIMEOUT=30000
```

Или создайте файл `application.properties` в `src/main/resources/` и укажите значения напрямую (не рекомендуется для production).

### 3. Сборка проекта

```bash
cd Task5TelegramBot
mvn clean package
```

### 4. Запуск

#### Запуск Python API сервера

В отдельном терминале:

```bash
cd Task5
python api_secure.py
```

Сервер должен запуститься на `http://localhost:8000` (или порт, указанный в переменных окружения).

#### Запуск Java приложения

```bash
cd Task5TelegramBot
mvn spring-boot:run
```

Или если проект уже собран:

```bash
java -jar target/task5-telegram-bot-1.0.0.jar
```

## Использование

1. Найдите вашего бота в Telegram по username
2. Отправьте команду `/start` или `/help`
3. Задайте вопрос о вселенной Star Wars
4. Бот вернет ответ на основе базы знаний

### Команды бота

- `/start` - приветствие и инструкции
- `/help` - справка по использованию
- `/health` - проверка состояния Python API сервера

## Структура проекта

```
Task5TelegramBot/
├── pom.xml                          # Maven конфигурация
├── README.md                        # Этот файл
└── src/
    └── main/
        ├── java/
        │   └── ru/yandex/architecture/telegrambot/
        │       ├── TelegramBotApplication.java    # Главный класс
        │       ├── TelegramBot.java               # Обработчик Telegram сообщений
        │       ├── config/                       # Конфигурация
        │       │   ├── BotConfig.java
        │       │   ├── PythonApiConfig.java
        │       │   ├── TelegramBotConfig.java
        │       │   └── WebClientConfig.java
        │       ├── dto/                          # DTO классы
        │       │   ├── QueryRequest.java
        │       │   └── QueryResponse.java
        │       └── service/                      # Сервисы
        │           └── PythonApiClient.java      # Клиент для Python API
        └── resources/
            └── application.properties            # Конфигурация приложения
```

## Архитектура

```
Telegram User
     |
     v
Telegram Bot (Java/Spring Boot)
     |
     v
Python API Server (FastAPI)
     |
     v
SecureRAGEngine (Python)
     |
     v
ChromaDB + YandexGPT
```

## Устранение проблем

### Бот не отвечает

1. Проверьте, что Python API сервер запущен и доступен
2. Проверьте правильность `TELEGRAM_BOT_TOKEN` и `TELEGRAM_BOT_USERNAME`
3. Проверьте логи приложения на наличие ошибок

### Ошибка подключения к Python API

1. Убедитесь, что Python API сервер запущен на правильном порту
2. Проверьте значение `PYTHON_API_URL` в конфигурации
3. Используйте команду `/health` для проверки доступности API

### Ошибки при сборке

1. Убедитесь, что используется Java 17+
2. Проверьте, что Maven установлен и доступен
3. Выполните `mvn clean install` для обновления зависимостей

## Разработка

### Запуск в режиме разработки

```bash
mvn spring-boot:run
```

### Тестирование

```bash
mvn test
```

