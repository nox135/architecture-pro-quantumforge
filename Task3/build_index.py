"""
Скрипт для создания векторного индекса базы знаний.
Использует BGE-base-en-v1.5 для генерации эмбеддингов и ChromaDB для хранения индекса.
"""

import os
import time
from pathlib import Path
from typing import List, Dict

from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import chromadb
from chromadb.config import Settings
from tqdm import tqdm


# Конфигурация
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
EMBEDDING_SIZE = 768  # Размер эмбеддингов для BGE-base-en-v1.5

# Определяем пути относительно текущего файла
SCRIPT_DIR = Path(__file__).parent.absolute()
KNOWLEDGE_BASE_PATH = SCRIPT_DIR.parent / "Task2" / "knowledge_base"
CHROMA_DB_PATH = SCRIPT_DIR / "chroma_db"
COLLECTION_NAME = "star_wars_knowledge_base"

# Параметры разбиения на чанки
CHUNK_SIZE = 1000  # ~500-1000 токенов
CHUNK_OVERLAP = 200  # Перекрытие для сохранения контекста


def load_documents(knowledge_base_path: Path) -> List[Document]:
    """
    Загружает все текстовые документы из базы знаний.
    
    Args:
        knowledge_base_path: Путь к папке с документами
        
    Returns:
        Список документов LangChain с метаданными
    """
    documents = []
    
    # Получаем все .txt файлы, исключая terms_map.json
    txt_files = list(knowledge_base_path.glob("*.txt"))
    
    print(f"Найдено {len(txt_files)} документов для обработки")
    
    for file_path in tqdm(txt_files, desc="Загрузка документов"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Извлекаем название статьи из имени файла
            title = file_path.stem.replace("_", " ")
            
            # Создаем документ с метаданными
            doc = Document(
                page_content=content,
                metadata={
                    "source": str(file_path),
                    "filename": file_path.name,
                    "title": title
                }
            )
            documents.append(doc)
        except Exception as e:
            print(f"Ошибка при загрузке {file_path}: {e}")
    
    return documents


def split_documents(documents: List[Document]) -> List[Document]:
    """
    Разбивает документы на логически связанные чанки.
    
    Args:
        documents: Список исходных документов
        
    Returns:
        Список чанков с метаданными
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    chunks = []
    chunk_id = 0
    
    for doc in tqdm(documents, desc="Разбиение на чанки"):
        doc_chunks = text_splitter.split_documents([doc])
        
        for chunk_index, chunk in enumerate(doc_chunks):
            # Добавляем информацию о позиции чанка
            chunk.metadata["chunk_id"] = chunk_id
            chunk.metadata["chunk_index"] = chunk_index
            chunk.metadata["total_chunks"] = len(doc_chunks)
            chunks.append(chunk)
            chunk_id += 1
    
    return chunks


def create_embeddings(chunks: List[Document], model: SentenceTransformer) -> List[List[float]]:
    """
    Генерирует эмбеддинги для всех чанков.
    
    Args:
        chunks: Список чанков
        model: Модель для генерации эмбеддингов
        
    Returns:
        Список векторов эмбеддингов
    """
    texts = [chunk.page_content for chunk in chunks]
    
    print(f"Генерация эмбеддингов для {len(texts)} чанков...")
    
    # Генерируем эмбеддинги батчами для оптимизации
    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        batch_size=32,
        convert_to_numpy=True  # Сначала получаем numpy массив
    )
    
    # Конвертируем numpy массив в список списков Python
    # Это гарантирует правильный формат для ChromaDB
    if hasattr(embeddings, 'tolist'):
        return embeddings.tolist()
    else:
        # Если уже список, конвертируем каждый элемент
        return [emb.tolist() if hasattr(emb, 'tolist') else list(emb) for emb in embeddings]


def build_index():
    """
    Основная функция для построения векторного индекса.
    """
    start_time = time.time()
    
    print("=" * 60)
    print("Создание векторного индекса базы знаний")
    print("=" * 60)
    print(f"Модель эмбеддингов: {EMBEDDING_MODEL}")
    print(f"Размер эмбеддингов: {EMBEDDING_SIZE}")
    print(f"Размер чанка: {CHUNK_SIZE} символов")
    print(f"Перекрытие чанков: {CHUNK_OVERLAP} символов")
    print()
    
    # Проверка существования базы знаний
    if not KNOWLEDGE_BASE_PATH.exists():
        print(f"Ошибка: База знаний не найдена по пути {KNOWLEDGE_BASE_PATH}")
        print("Убедитесь, что Task2/knowledge_base/ существует и содержит документы")
        return
    
    # 1. Загрузка документов
    print("Шаг 1: Загрузка документов из базы знаний...")
    documents = load_documents(KNOWLEDGE_BASE_PATH)
    
    if len(documents) == 0:
        print("Ошибка: Не найдено документов для обработки")
        return
    
    print(f"Загружено документов: {len(documents)}")
    print()
    
    # 2. Разбиение на чанки
    print("Шаг 2: Разбиение документов на чанки...")
    chunks = split_documents(documents)
    print(f"Создано чанков: {len(chunks)}")
    print()
    
    # 3. Загрузка модели эмбеддингов
    print("Шаг 3: Загрузка модели эмбеддингов...")
    embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    print("Модель загружена")
    print()
    
    # 4. Генерация эмбеддингов
    print("Шаг 4: Генерация эмбеддингов...")
    embeddings = create_embeddings(chunks, embedding_model)
    print(f"Сгенерировано эмбеддингов: {len(embeddings)}")
    print()
    
    # 5. Создание ChromaDB индекса
    print("Шаг 5: Создание векторного индекса в ChromaDB...")
    
    # Удаляем существующую БД, если есть
    if CHROMA_DB_PATH.exists():
        import shutil
        shutil.rmtree(CHROMA_DB_PATH)
        print("Удалена существующая база данных")
    
    # Создаем клиент ChromaDB
    client = chromadb.PersistentClient(
        path=str(CHROMA_DB_PATH),
        settings=Settings(anonymized_telemetry=False)
    )
    
    # Создаем или получаем коллекцию
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "Star Wars knowledge base vector index"}
    )
    
    # Подготавливаем данные для добавления
    ids = [f"chunk_{i}" for i in range(len(chunks))]
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
    
    # Добавляем данные в коллекцию батчами (ChromaDB имеет ограничение на размер батча)
    print("Добавление чанков в индекс...")
    BATCH_SIZE = 5000  # Безопасный размер батча для ChromaDB
    
    total_chunks = len(chunks)
    for i in tqdm(range(0, total_chunks, BATCH_SIZE), desc="Добавление батчей"):
        end_idx = min(i + BATCH_SIZE, total_chunks)
        batch_ids = ids[i:end_idx]
        batch_embeddings = embeddings[i:end_idx]
        batch_texts = texts[i:end_idx]
        batch_metadatas = metadatas[i:end_idx]
        
        collection.add(
            ids=batch_ids,
            embeddings=batch_embeddings,
            documents=batch_texts,
            metadatas=batch_metadatas
        )
    
    print(f"Индекс создан: {len(ids)} чанков добавлено")
    print()
    
    # Статистика
    elapsed_time = time.time() - start_time
    print("=" * 60)
    print("Индексация завершена!")
    print("=" * 60)
    print(f"Время выполнения: {elapsed_time:.2f} секунд ({elapsed_time/60:.2f} минут)")
    print(f"Документов обработано: {len(documents)}")
    print(f"Чанков создано: {len(chunks)}")
    print(f"Среднее чанков на документ: {len(chunks)/len(documents):.2f}")
    print(f"Путь к индексу: {CHROMA_DB_PATH.absolute()}")
    print()
    
    # Сохраняем статистику
    stats = {
        "model": EMBEDDING_MODEL,
        "embedding_size": EMBEDDING_SIZE,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "documents_count": len(documents),
        "chunks_count": len(chunks),
        "indexing_time_seconds": elapsed_time,
        "index_path": str(CHROMA_DB_PATH.absolute())
    }
    
    import json
    with open("index_stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    print("Статистика сохранена в index_stats.json")


if __name__ == "__main__":
    build_index()

