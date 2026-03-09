# RAG-бот с техниками промптинга

Реализация RAG-бота с применением техник Few-shot prompting и Chain-of-Thought для улучшения качества ответов.

## Структура проекта

```
Task4/
├── config.py          # Конфигурация (пути, модели, параметры)
├── rag_engine.py      # Основной модуль RAG-движка
├── api.py             # REST API на FastAPI
├── requirements.txt   # Зависимости
├── examples.md        # Примеры использования
└── README.md          # Документация
```

## Установка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Убедитесь, что векторный индекс создан (Task3/build_index.py должен быть выполнен)

3. Настройте конфигурацию через `.env` файл:
   - Создайте файл `.env/gpt_api` в корне проекта (или скопируйте `Task4/env.example`)
   - Файл должен содержать обязательные параметры:
     - `YANDEX_API_KEY` - ваш API ключ Yandex Cloud
     - `YANDEX_FOLDER_ID` - ID вашего каталога в Yandex Cloud
   - Пример содержимого файла `.env/gpt_api`:
     ```
     YANDEX_API_KEY=your-api-key-here
     YANDEX_FOLDER_ID=your-folder-id-here
     ```
   - Система автоматически ищет файл в следующих местах:
     - `.env/gpt_api` (в корне проекта)
     - `.env/gpt_api.env`
     - `.env/.env`
     - `Task4/.env`
   - Остальные параметры имеют значения по умолчанию и могут быть изменены при необходимости

Альтернативно, можно использовать переменные окружения напрямую:
```bash
# Windows PowerShell
$env:YANDEX_API_KEY="your-api-key"
$env:YANDEX_FOLDER_ID="your-folder-id"

# Linux/Mac
export YANDEX_API_KEY="your-api-key"
export YANDEX_FOLDER_ID="your-folder-id"
```

## Запуск

### Запуск REST API сервера

```bash
python api.py
```

Сервер запустится на `http://localhost:8000`

### Использование API

#### Проверка здоровья сервиса
```bash
curl http://localhost:8000/health
```

#### Отправка запроса

**Вариант 1: Использование Python скрипта (рекомендуется)**
```bash
python test_api.py
```

**Вариант 2: PowerShell (Invoke-RestMethod)**
```powershell
$body = @{
    query = "Что такое Сила?"
    top_k = 3
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/query" -Method POST -Body $body -ContentType "application/json"
```

**Вариант 3: curl (Linux/Mac или Git Bash)**
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Что такое Сила?", "top_k": 3}'
```

**Вариант 4: curl.exe в PowerShell (одной строкой)**
```powershell
curl.exe -X POST "http://localhost:8000/query" -H "Content-Type: application/json" -d '{\"query\": \"Что такое Сила?\", \"top_k\": 3}'
```

#### Документация API
Откройте в браузере: `http://localhost:8000/docs` (Swagger UI)

## Особенности реализации

### 1. RAG пайплайн
- Загрузка векторного индекса из ChromaDB
- Преобразование запроса в эмбеддинг (BGE-base-en-v1.5)
- Поиск релевантных чанков в векторной базе
- Формирование промпта с найденными фрагментами
- Генерация ответа через YandexGPT

### 2. Few-shot prompting
- Автоматическое извлечение примеров из базы знаний
- Добавление 1-2 примеров вопрос-ответ в промпт
- Примеры берутся из той же предметной области

### 3. Chain-of-Thought (CoT)
- System-промпт с инструкциями для пошагового рассуждения
- Модель объясняет свои шаги перед ответом
- Структурированный формат: анализ → поиск → вывод

### 4. Обработка случаев "Я не знаю"
- Проверка релевантности найденных чанков
- Порог релевантности (косинусное расстояние)
- Честный ответ при отсутствии информации

## Конфигурация

Настройки загружаются из переменных окружения или `.env` файла. Все параметры имеют значения по умолчанию, кроме обязательных для YandexGPT.

### Обязательные параметры:
- `YANDEX_API_KEY` - API ключ Yandex Cloud
- `YANDEX_FOLDER_ID` - ID каталога в Yandex Cloud

### Опциональные параметры (со значениями по умолчанию):
- `COLLECTION_NAME` - название коллекции в ChromaDB (по умолчанию: `star_wars_knowledge_base`)
- `EMBEDDING_MODEL` - модель для генерации эмбеддингов (по умолчанию: `BAAI/bge-base-en-v1.5`)
- `TOP_K` - количество релевантных чанков для поиска (по умолчанию: `3`)
- `YANDEX_MODEL` - модель YandexGPT (по умолчанию: `yandexgpt-lite`)
- `YANDEX_TEMPERATURE` - температура генерации (по умолчанию: `0.7`)
- `YANDEX_MAX_TOKENS` - максимальное количество токенов (по умолчанию: `1000`)
- `RELEVANCE_THRESHOLD` - порог релевантности (по умолчанию: `0.8`)

Путь к векторной базе данных (`CHROMA_DB_PATH`) настраивается в `config.py` и указывает на `Task3/chroma_db`.

## Примеры

См. файл `examples.md` с примерами успешных диалогов и случаев "Я не знаю".

## Технологии

- **ChromaDB** - векторная база данных
- **Sentence Transformers** - генерация эмбеддингов
- **FastAPI** - REST API фреймворк
- **YandexGPT** - языковая модель



