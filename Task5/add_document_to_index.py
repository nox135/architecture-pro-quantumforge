"""
Скрипт для добавления отдельного документа в существующую векторную базу.
Используется для добавления злонамеренного файла в базу знаний.
"""

import sys
from pathlib import Path
from typing import List

from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import chromadb
from chromadb.config import Settings
from tqdm import tqdm

# Конфигурация (должна совпадать с Task3/build_index.py)
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Пути
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent
CHROMA_DB_PATH = PROJECT_ROOT / "Task3" / "chroma_db"
COLLECTION_NAME = "star_wars_knowledge_base"


def load_single_document(file_path: Path) -> Document:
    """
    Загружает один документ из файла.
    
    Args:
        file_path: Путь к файлу
        
    Returns:
        Документ LangChain с метаданными
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Файл не найден: {file_path}")
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Извлекаем название из имени файла
    title = file_path.stem.replace("_", " ")
    
    doc = Document(
        page_content=content,
        metadata={
            "source": str(file_path),
            "filename": file_path.name,
            "title": title
        }
    )
    
    return doc


def split_document(doc: Document) -> List[Document]:
    """
    Разбивает документ на чанки.
    
    Args:
        doc: Исходный документ
        
    Returns:
        Список чанков с метаданными
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    chunks = text_splitter.split_documents([doc])
    
    # Добавляем метаданные о позиции чанка
    for chunk_index, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = f"malicious_{chunk_index}"
        chunk.metadata["chunk_index"] = chunk_index
        chunk.metadata["total_chunks"] = len(chunks)
    
    return chunks


def add_document_to_index(file_path: Path):
    """
    Добавляет документ в существующую векторную базу.
    
    Args:
        file_path: Путь к файлу для добавления
    """
    print("=" * 60)
    print("Добавление документа в векторную базу")
    print("=" * 60)
    print(f"Файл: {file_path}")
    print()
    
    # Проверка существования базы данных
    if not CHROMA_DB_PATH.exists():
        print(f"Ошибка: Векторная база данных не найдена по пути {CHROMA_DB_PATH}")
        print("Сначала запустите Task3/build_index.py для создания индекса")
        return
    
    # 1. Загрузка документа
    print("Шаг 1: Загрузка документа...")
    doc = load_single_document(file_path)
    print(f"Загружен документ: {doc.metadata['title']}")
    print(f"Размер: {len(doc.page_content)} символов")
    print()
    
    # 2. Разбиение на чанки
    print("Шаг 2: Разбиение документа на чанки...")
    chunks = split_document(doc)
    print(f"Создано чанков: {len(chunks)}")
    print()
    
    # 3. Загрузка модели эмбеддингов
    print("Шаг 3: Загрузка модели эмбеддингов...")
    embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    print("Модель загружена")
    print()
    
    # 4. Генерация эмбеддингов
    print("Шаг 4: Генерация эмбеддингов...")
    texts = [chunk.page_content for chunk in chunks]
    embeddings = embedding_model.encode(
        texts,
        show_progress_bar=True,
        batch_size=32,
        convert_to_numpy=True
    )
    
    if hasattr(embeddings, 'tolist'):
        embeddings = embeddings.tolist()
    else:
        embeddings = [emb.tolist() if hasattr(emb, 'tolist') else list(emb) for emb in embeddings]
    
    print(f"Сгенерировано эмбеддингов: {len(embeddings)}")
    print()
    
    # 5. Подключение к существующей базе
    print("Шаг 5: Подключение к векторной базе данных...")
    client = chromadb.PersistentClient(
        path=str(CHROMA_DB_PATH),
        settings=Settings(anonymized_telemetry=False)
    )
    
    # Получаем существующую коллекцию
    try:
        collection = client.get_collection(name=COLLECTION_NAME)
        print(f"Коллекция '{COLLECTION_NAME}' найдена")
    except Exception as e:
        print(f"Ошибка: Коллекция '{COLLECTION_NAME}' не найдена")
        print("Сначала запустите Task3/build_index.py для создания индекса")
        return
    
    # Получаем текущее количество чанков для генерации уникальных ID
    current_count = collection.count()
    print(f"Текущее количество чанков в базе: {current_count}")
    print()
    
    # 6. Добавление в базу
    print("Шаг 6: Добавление чанков в индекс...")
    ids = [f"chunk_{current_count + i}" for i in range(len(chunks))]
    texts = [chunk.page_content for chunk in chunks]
    metadatas = [
        {
            "source": chunk.metadata["source"],
            "filename": chunk.metadata["filename"],
            "title": chunk.metadata["title"],
            "chunk_id": chunk.metadata["chunk_id"],
            "chunk_index": chunk.metadata["chunk_index"],
            "total_chunks": chunk.metadata["total_chunks"]
        }
        for chunk in chunks
    ]
    
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas
    )
    
    print(f"Добавлено чанков: {len(ids)}")
    print(f"Новое количество чанков в базе: {collection.count()}")
    print()
    print("=" * 60)
    print("Документ успешно добавлен в векторную базу!")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])
    else:
        # По умолчанию используем злонамеренный файл
        file_path = SCRIPT_DIR / "malicious_document.txt"
    
    if not file_path.is_absolute():
        file_path = SCRIPT_DIR / file_path
    
    add_document_to_index(file_path)

