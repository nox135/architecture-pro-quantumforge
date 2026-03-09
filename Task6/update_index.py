"""
Скрипт для автоматического обновления векторного индекса базы знаний.
Сканирует источник данных, находит новые или измененные документы,
обновляет векторную БД и логирует процесс.
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set, Tuple
from hashlib import md5

from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import chromadb
from chromadb.config import Settings
from tqdm import tqdm


# Конфигурация
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
EMBEDDING_SIZE = 768
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Пути
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent
KNOWLEDGE_BASE_PATH = PROJECT_ROOT / "Task2" / "knowledge_base"
CHROMA_DB_PATH = PROJECT_ROOT / "Task3" / "chroma_db"
COLLECTION_NAME = "star_wars_knowledge_base"
LOG_DIR = SCRIPT_DIR / "logs"
STATE_FILE = SCRIPT_DIR / "update_state.json"  # Файл для отслеживания обработанных файлов

# Настройка логирования
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"update_index_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def load_state() -> Dict:
    """Загружает состояние последнего обновления."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Ошибка при загрузке состояния: {e}. Создаю новое состояние.")
    return {
        "last_update": None,
        "processed_files": {}  # {filename: {"hash": hash, "mtime": mtime, "chunks_count": count}}
    }


def save_state(state: Dict):
    """Сохраняет состояние обновления."""
    try:
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Ошибка при сохранении состояния: {e}")


def get_file_hash(file_path: Path) -> str:
    """Вычисляет MD5 хеш файла."""
    hash_md5 = md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def find_new_or_modified_files(knowledge_base_path: Path, state: Dict) -> List[Tuple[Path, bool]]:
    """
    Находит новые или измененные файлы.
    
    Returns:
        Список кортежей (путь_к_файлу, is_new)
    """
    if not knowledge_base_path.exists():
        logger.error(f"База знаний не найдена: {knowledge_base_path}")
        return []
    
    txt_files = list(knowledge_base_path.glob("*.txt"))
    new_or_modified = []
    processed_files = state.get("processed_files", {})
    
    for file_path in txt_files:
        filename = file_path.name
        current_hash = get_file_hash(file_path)
        current_mtime = file_path.stat().st_mtime
        
        if filename not in processed_files:
            # Новый файл
            new_or_modified.append((file_path, True))
            logger.info(f"Найден новый файл: {filename}")
        else:
            # Проверяем, изменился ли файл
            old_info = processed_files[filename]
            if (old_info.get("hash") != current_hash or 
                old_info.get("mtime") != current_mtime):
                new_or_modified.append((file_path, False))
                logger.info(f"Найден измененный файл: {filename}")
    
    return new_or_modified


def load_document(file_path: Path) -> Document:
    """Загружает документ из файла."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
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
    except Exception as e:
        logger.error(f"Ошибка при загрузке {file_path}: {e}")
        raise


def split_document(doc: Document) -> List[Document]:
    """Разбивает документ на чанки."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    chunks = text_splitter.split_documents([doc])
    
    # Добавляем метаданные о позиции чанка
    for chunk_index, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = chunk_index
        chunk.metadata["total_chunks"] = len(chunks)
    
    return chunks


def remove_old_chunks_for_file(collection, filename: str):
    """Удаляет старые чанки для файла из индекса."""
    try:
        # Получаем все чанки с данным filename
        results = collection.get(
            where={"filename": filename}
        )
        
        if results and len(results["ids"]) > 0:
            collection.delete(ids=results["ids"])
            logger.info(f"Удалено {len(results['ids'])} старых чанков для файла {filename}")
            return len(results["ids"])
    except Exception as e:
        logger.warning(f"Ошибка при удалении старых чанков для {filename}: {e}")
    
    return 0


def update_index():
    """Основная функция обновления индекса."""
    start_time = time.time()
    start_datetime = datetime.now()
    
    logger.info("=" * 60)
    logger.info("Начало обновления векторного индекса")
    logger.info("=" * 60)
    logger.info(f"Время запуска: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Источник данных: {KNOWLEDGE_BASE_PATH}")
    logger.info(f"Векторная БД: {CHROMA_DB_PATH}")
    logger.info("")
    
    # Проверка существования базы знаний
    if not KNOWLEDGE_BASE_PATH.exists():
        logger.error(f"База знаний не найдена: {KNOWLEDGE_BASE_PATH}")
        return {
            "success": False,
            "error": "База знаний не найдена",
            "new_chunks": 0,
            "updated_files": 0,
            "total_chunks": 0
        }
    
    # Проверка существования векторной БД
    if not CHROMA_DB_PATH.exists():
        logger.error(f"Векторная БД не найдена: {CHROMA_DB_PATH}")
        logger.error("Сначала запустите Task3/build_index.py для создания индекса")
        return {
            "success": False,
            "error": "Векторная БД не найдена",
            "new_chunks": 0,
            "updated_files": 0,
            "total_chunks": 0
        }
    
    # Загрузка состояния
    state = load_state()
    
    # Поиск новых и измененных файлов
    logger.info("Сканирование источника данных...")
    files_to_process = find_new_or_modified_files(KNOWLEDGE_BASE_PATH, state)
    
    if not files_to_process:
        logger.info("Новых или измененных файлов не найдено")
        # Получаем текущий размер индекса
        try:
            client = chromadb.PersistentClient(
                path=str(CHROMA_DB_PATH),
                settings=Settings(anonymized_telemetry=False)
            )
            collection = client.get_collection(name=COLLECTION_NAME)
            total_chunks = collection.count()
            logger.info(f"Текущий размер индекса: {total_chunks} чанков")
        except Exception as e:
            logger.warning(f"Не удалось получить размер индекса: {e}")
            total_chunks = 0
        
        elapsed_time = time.time() - start_time
        logger.info(f"Время выполнения: {elapsed_time:.2f} секунд")
        logger.info("Обновление завершено (нет изменений)")
        
        return {
            "success": True,
            "new_chunks": 0,
            "updated_files": 0,
            "total_chunks": total_chunks,
            "elapsed_time": elapsed_time
        }
    
    logger.info(f"Найдено файлов для обработки: {len(files_to_process)}")
    logger.info("")
    
    # Загрузка модели эмбеддингов
    logger.info("Загрузка модели эмбеддингов...")
    try:
        embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        logger.info("Модель загружена")
    except Exception as e:
        logger.error(f"Ошибка при загрузке модели: {e}")
        return {
            "success": False,
            "error": f"Ошибка загрузки модели: {e}",
            "new_chunks": 0,
            "updated_files": 0,
            "total_chunks": 0
        }
    
    # Подключение к векторной БД
    logger.info("Подключение к векторной БД...")
    try:
        client = chromadb.PersistentClient(
            path=str(CHROMA_DB_PATH),
            settings=Settings(anonymized_telemetry=False)
        )
        collection = client.get_collection(name=COLLECTION_NAME)
        initial_chunks_count = collection.count()
        logger.info(f"Текущий размер индекса: {initial_chunks_count} чанков")
    except Exception as e:
        logger.error(f"Ошибка при подключении к БД: {e}")
        return {
            "success": False,
            "error": f"Ошибка подключения к БД: {e}",
            "new_chunks": 0,
            "updated_files": 0,
            "total_chunks": 0
        }
    
    # Обработка файлов
    total_new_chunks = 0
    processed_count = 0
    errors = []
    
    for file_path, is_new in tqdm(files_to_process, desc="Обработка файлов"):
        try:
            filename = file_path.name
            logger.info(f"Обработка файла: {filename} ({'новый' if is_new else 'измененный'})")
            
            # Если файл изменен, удаляем старые чанки
            if not is_new:
                removed_count = remove_old_chunks_for_file(collection, filename)
                logger.info(f"Удалено старых чанков: {removed_count}")
            
            # Загрузка документа
            doc = load_document(file_path)
            
            # Разбиение на чанки
            chunks = split_document(doc)
            logger.info(f"Создано чанков: {len(chunks)}")
            
            # Генерация эмбеддингов
            texts = [chunk.page_content for chunk in chunks]
            embeddings = embedding_model.encode(
                texts,
                show_progress_bar=False,
                batch_size=32,
                convert_to_numpy=True
            )
            
            if hasattr(embeddings, 'tolist'):
                embeddings = embeddings.tolist()
            else:
                embeddings = [emb.tolist() if hasattr(emb, 'tolist') else list(emb) for emb in embeddings]
            
            # Получаем текущее количество чанков для генерации уникальных ID
            current_count = collection.count()
            ids = [f"chunk_{current_count + i}" for i in range(len(chunks))]
            
            # Подготовка метаданных
            metadatas = [
                {
                    "source": chunk.metadata["source"],
                    "filename": chunk.metadata["filename"],
                    "title": chunk.metadata["title"],
                    "chunk_index": chunk.metadata["chunk_index"],
                    "total_chunks": chunk.metadata["total_chunks"]
                }
                for chunk in chunks
            ]
            
            # Добавление в индекс
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )
            
            total_new_chunks += len(chunks)
            processed_count += 1
            
            # Обновление состояния
            file_hash = get_file_hash(file_path)
            file_mtime = file_path.stat().st_mtime
            state["processed_files"][filename] = {
                "hash": file_hash,
                "mtime": file_mtime,
                "chunks_count": len(chunks),
                "last_processed": datetime.now().isoformat()
            }
            
            logger.info(f"Файл {filename} успешно обработан: добавлено {len(chunks)} чанков")
            
        except Exception as e:
            error_msg = f"Ошибка при обработке {file_path.name}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
    
    # Сохранение состояния
    state["last_update"] = start_datetime.isoformat()
    save_state(state)
    
    # Финальная статистика
    final_chunks_count = collection.count()
    elapsed_time = time.time() - start_time
    end_datetime = datetime.now()
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("Обновление завершено")
    logger.info("=" * 60)
    logger.info(f"Время завершения: {end_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Время выполнения: {elapsed_time:.2f} секунд ({elapsed_time/60:.2f} минут)")
    logger.info(f"Обработано файлов: {processed_count} из {len(files_to_process)}")
    logger.info(f"Добавлено новых чанков: {total_new_chunks}")
    logger.info(f"Размер индекса до обновления: {initial_chunks_count} чанков")
    logger.info(f"Размер индекса после обновления: {final_chunks_count} чанков")
    logger.info(f"Ошибок: {len(errors)}")
    
    if errors:
        logger.error("Список ошибок:")
        for error in errors:
            logger.error(f"  - {error}")
    
    # Сохранение результата в JSON
    result = {
        "success": len(errors) == 0,
        "start_time": start_datetime.isoformat(),
        "end_time": end_datetime.isoformat(),
        "elapsed_time_seconds": elapsed_time,
        "updated_files": processed_count,
        "new_chunks": total_new_chunks,
        "initial_chunks_count": initial_chunks_count,
        "final_chunks_count": final_chunks_count,
        "errors": errors
    }
    
    result_file = LOG_DIR / f"update_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Результат сохранен в: {result_file}")
    
    return result


if __name__ == "__main__":
    try:
        result = update_index()
        if result["success"]:
            sys.exit(0)
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("Обновление прервано пользователем")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)

