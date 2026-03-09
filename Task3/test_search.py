"""
Скрипт для тестирования поиска в векторном индексе.
Демонстрирует примеры запросов и найденные релевантные чанки.
"""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from pathlib import Path


# Конфигурация
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"

# Определяем пути относительно текущего файла
SCRIPT_DIR = Path(__file__).parent.absolute()
CHROMA_DB_PATH = SCRIPT_DIR / "chroma_db"
COLLECTION_NAME = "star_wars_knowledge_base"
TOP_K = 3  # Количество результатов для каждого запроса


def search_query(query: str, collection, embedding_model, top_k: int = TOP_K):
    """
    Выполняет поиск по запросу в векторном индексе.
    
    Args:
        query: Текстовый запрос
        collection: Коллекция ChromaDB
        embedding_model: Модель для генерации эмбеддингов запроса
        top_k: Количество результатов
        
    Returns:
        Список найденных чанков с метаданными
    """
    # Генерируем эмбеддинг для запроса
    query_embedding = embedding_model.encode(query, convert_to_numpy=False).tolist()
    
    # Выполняем поиск
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k
    )
    
    return results


def format_results(results: dict, query: str):
    """
    Форматирует результаты поиска для вывода.
    
    Args:
        results: Результаты поиска из ChromaDB
        query: Исходный запрос
    """
    print("=" * 80)
    print(f"Запрос: {query}")
    print("=" * 80)
    print()
    
    if not results["ids"] or len(results["ids"][0]) == 0:
        print("Результаты не найдены")
        return
    
    for i, (doc_id, doc_text, metadata, distance) in enumerate(
        zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0] if "distances" in results else [None] * len(results["ids"][0])
        ),
        start=1
    ):
        print(f"Результат #{i}")
        print(f"  Файл: {metadata['filename']}")
        print(f"  Заголовок: {metadata['title']}")
        print(f"  Чанк: {metadata['chunk_index'] + 1}/{metadata['total_chunks']}")
        if distance is not None:
            print(f"  Расстояние (косинусное): {distance:.4f}")
        print(f"  Текст чанка:")
        print(f"  {'-' * 76}")
        # Показываем первые 500 символов чанка
        preview = doc_text[:500] + "..." if len(doc_text) > 500 else doc_text
        print(f"  {preview}")
        print()
        print()


def test_search():
    """
    Основная функция для тестирования поиска.
    """
    print("=" * 80)
    print("Тестирование поиска в векторном индексе")
    print("=" * 80)
    print()
    
    # Проверяем наличие индекса
    if not CHROMA_DB_PATH.exists():
        print(f"Ошибка: Индекс не найден в {CHROMA_DB_PATH}")
        print("Сначала запустите build_index.py для создания индекса")
        return
    
    # Загружаем модель эмбеддингов
    print("Загрузка модели эмбеддингов...")
    embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    print("Модель загружена")
    print()
    
    # Подключаемся к ChromaDB
    print("Подключение к векторной базе данных...")
    client = chromadb.PersistentClient(
        path=str(CHROMA_DB_PATH),
        settings=Settings(anonymized_telemetry=False)
    )
    
    collection = client.get_collection(name=COLLECTION_NAME)
    print(f"Коллекция '{COLLECTION_NAME}' загружена")
    
    # Получаем статистику
    count = collection.count()
    print(f"Всего чанков в индексе: {count}")
    print()
    
    # Примеры запросов для тестирования
    test_queries = [
        "What is the Force and how does it work?",
        "Tell me about Luke Skywalker's training",
        "What is a lightsaber and how is it constructed?",
        "Who is Darth Vader and what is his story?",
        "What is the Death Star?"
    ]
    
    print("Выполнение тестовых запросов...")
    print()
    
    # Выполняем поиск для каждого запроса
    for query in test_queries:
        results = search_query(query, collection, embedding_model, TOP_K)
        format_results(results, query)
        print()
    
    print("=" * 80)
    print("Тестирование завершено")
    print("=" * 80)


if __name__ == "__main__":
    test_search()

