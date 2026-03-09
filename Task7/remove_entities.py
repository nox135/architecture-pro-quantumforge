"""
Скрипт для удаления ключевых сущностей из векторного индекса.
Создает искусственные пробелы в базе знаний для тестирования качества RAG-бота.
"""

import sys
from pathlib import Path
import chromadb
from chromadb.config import Settings

# Добавляем путь к Task4 для импорта конфигурации
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT / "Task4"))

from config import CHROMA_DB_PATH, COLLECTION_NAME

# Сущности для удаления (по названиям файлов/документов)
ENTITIES_TO_REMOVE = [
    "Yoda",  # Удаляем информацию о Йоде
    "Death Star",  # Удаляем информацию о Звезде Смерти
    "Darth Vader",  # Удаляем информацию о Дарте Вейдере
]


def remove_entities_from_index():
    """
    Удаляет указанные сущности из векторного индекса ChromaDB.
    """
    print("=" * 60)
    print("Удаление сущностей из векторного индекса")
    print("=" * 60)
    
    if not CHROMA_DB_PATH.exists():
        print(f"Ошибка: Векторная база данных не найдена по пути {CHROMA_DB_PATH}")
        print("Сначала запустите Task3/build_index.py для создания индекса.")
        return
    
    # Подключение к ChromaDB
    print("Подключение к векторной базе данных...")
    client = chromadb.PersistentClient(
        path=str(CHROMA_DB_PATH),
        settings=Settings(anonymized_telemetry=False)
    )
    
    try:
        collection = client.get_collection(name=COLLECTION_NAME)
    except Exception as e:
        print(f"Ошибка при получении коллекции: {e}")
        return
    
    print(f"Коллекция '{COLLECTION_NAME}' загружена")
    
    # Получаем все документы из коллекции
    all_data = collection.get()
    
    if not all_data["ids"]:
        print("Коллекция пуста")
        return
    
    print(f"Всего чанков в индексе: {len(all_data['ids'])}")
    
    # Находим чанки, которые нужно удалить
    ids_to_remove = []
    removed_count = 0
    
    for entity in ENTITIES_TO_REMOVE:
        print(f"\nПоиск чанков для удаления: {entity}")
        
        # Ищем чанки, где title содержит название сущности
        for i, metadata in enumerate(all_data["metadatas"]):
            title = metadata.get("title", "").lower()
            filename = metadata.get("filename", "").lower()
            
            # Проверяем совпадение по title или filename
            if entity.lower() in title or entity.lower().replace(" ", "_") in filename:
                chunk_id = all_data["ids"][i]
                if chunk_id not in ids_to_remove:
                    ids_to_remove.append(chunk_id)
                    removed_count += 1
                    print(f"  Найден чанк для удаления: {chunk_id} (источник: {metadata.get('title', 'Unknown')})")
    
    if not ids_to_remove:
        print("\nНе найдено чанков для удаления. Возможно, сущности уже удалены или не существуют.")
        return
    
    print(f"\nВсего найдено чанков для удаления: {len(ids_to_remove)}")
    
    # Удаляем чанки
    print("\nУдаление чанков из индекса...")
    collection.delete(ids=ids_to_remove)
    
    print("=" * 60)
    print("Удаление завершено!")
    print("=" * 60)
    print(f"Удалено чанков: {len(ids_to_remove)}")
    print(f"Удаленные сущности: {', '.join(ENTITIES_TO_REMOVE)}")
    
    # Проверяем оставшееся количество
    remaining_data = collection.get()
    print(f"Осталось чанков в индексе: {len(remaining_data['ids'])}")
    
    # Сохраняем информацию об удалении
    import json
    removal_info = {
        "removed_entities": ENTITIES_TO_REMOVE,
        "removed_chunks_count": len(ids_to_remove),
        "remaining_chunks_count": len(remaining_data["ids"]),
        "removed_chunk_ids": ids_to_remove[:10]  # Первые 10 для примера
    }
    
    info_file = SCRIPT_DIR / "removal_info.json"
    with open(info_file, "w", encoding="utf-8") as f:
        json.dump(removal_info, f, indent=2, ensure_ascii=False)
    
    print(f"\nИнформация об удалении сохранена в {info_file}")


if __name__ == "__main__":
    remove_entities_from_index()

