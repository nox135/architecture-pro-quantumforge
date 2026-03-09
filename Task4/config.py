"""
Конфигурация для RAG-бота.
Параметры загружаются из переменных окружения или .env файла.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Пути
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent
CHROMA_DB_PATH = PROJECT_ROOT / "Task3" / "chroma_db"

# Загрузка переменных из .env файла
# Пробуем несколько вариантов путей
env_paths = [
    PROJECT_ROOT / ".env" / "gpt_api",  # .env/gpt_api (без расширения)
    PROJECT_ROOT / ".env" / "gpt_api.env",  # .env/gpt_api.env
    PROJECT_ROOT / ".env" / ".env",  # .env/.env
    SCRIPT_DIR / ".env",  # Task4/.env
    PROJECT_ROOT / ".env",  # корень/.env
]

ENV_FILE_PATH = None
for path in env_paths:
    if path.exists():
        ENV_FILE_PATH = path
        load_dotenv(dotenv_path=path)
        print(f"✓ Загружены переменные из {path}")
        break

if ENV_FILE_PATH is None:
    # Fallback: попытка загрузить из текущей директории
    load_dotenv()
    print("⚠ Файл .env не найден в стандартных местах, используется загрузка из переменных окружения")
    print("   Создайте файл .env/gpt_api в корне проекта со следующим содержимым:")
    print("   YANDEX_API_KEY=your-api-key")
    print("   YANDEX_FOLDER_ID=your-folder-id")

COLLECTION_NAME = os.getenv("COLLECTION_NAME", "star_wars_knowledge_base")

# Модель эмбеддингов (должна совпадать с той, что использовалась при создании индекса)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")

# Параметры поиска
TOP_K = int(os.getenv("TOP_K", "3"))  # Количество релевантных чанков для извлечения

# Параметры LLM (YandexGPT)
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")
YANDEX_MODEL = os.getenv("YANDEX_MODEL", "yandexgpt/latest")
YANDEX_TEMPERATURE = float(os.getenv("YANDEX_TEMPERATURE", "0.7"))
YANDEX_MAX_TOKENS = int(os.getenv("YANDEX_MAX_TOKENS", "1000"))

# Отладочная информация (без вывода самих ключей)
if YANDEX_API_KEY:
    print(f"✓ YANDEX_API_KEY загружен (длина: {len(YANDEX_API_KEY)} символов)")
else:
    print("✗ YANDEX_API_KEY не найден")
if YANDEX_FOLDER_ID:
    print(f"✓ YANDEX_FOLDER_ID загружен: {YANDEX_FOLDER_ID}")
else:
    print("✗ YANDEX_FOLDER_ID не найден")
print(f"Используемая модель: {YANDEX_MODEL}")

# Порог релевантности (если расстояние больше, считаем что информации нет)
RELEVANCE_THRESHOLD = float(os.getenv("RELEVANCE_THRESHOLD", "0.8"))  # Косинусное расстояние (чем больше, тем менее релевантно)

# Параметры API сервера
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))



