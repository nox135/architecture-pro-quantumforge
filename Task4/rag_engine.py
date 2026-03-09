"""
Модуль RAG-движка для поиска информации и генерации ответов.
Реализует Few-shot prompting и Chain-of-Thought.
"""

from typing import List, Dict, Optional, Tuple
from pathlib import Path
import json

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import requests

from config import (
    CHROMA_DB_PATH,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    TOP_K,
    RELEVANCE_THRESHOLD,
    YANDEX_API_KEY,
    YANDEX_FOLDER_ID,
    YANDEX_MODEL,
    YANDEX_TEMPERATURE,
    YANDEX_MAX_TOKENS
)


class RAGEngine:
    """
    RAG-движок для поиска информации в векторной базе и генерации ответов.
    """
    
    def __init__(self):
        """Инициализация RAG-движка."""
        # Загрузка модели эмбеддингов
        print("Загрузка модели эмбеддингов...")
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        print("Модель эмбеддингов загружена")
        
        # Подключение к ChromaDB
        if not CHROMA_DB_PATH.exists():
            raise FileNotFoundError(
                f"Векторная база данных не найдена по пути {CHROMA_DB_PATH}. "
                "Сначала запустите Task3/build_index.py для создания индекса."
            )
        
        print("Подключение к векторной базе данных...")
        self.client = chromadb.PersistentClient(
            path=str(CHROMA_DB_PATH),
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_collection(name=COLLECTION_NAME)
        print(f"Коллекция '{COLLECTION_NAME}' загружена")
        
        # Инициализация LLM клиента (YandexGPT)
        self._init_llm()
        
        # Few-shot примеры (извлекаются из базы при первом использовании)
        self.few_shot_examples: Optional[List[Tuple[str, str]]] = None
        
    def _init_llm(self):
        """Инициализация клиента LLM (YandexGPT)."""
        if not YANDEX_API_KEY or not YANDEX_FOLDER_ID:
            raise ValueError(
                "Не настроен API ключ для YandexGPT. "
                "Установите переменные окружения YANDEX_API_KEY и YANDEX_FOLDER_ID "
                "или добавьте их в .env файл"
            )
        
        self.yandex_api_key = YANDEX_API_KEY
        self.yandex_folder_id = YANDEX_FOLDER_ID
        print("Используется YandexGPT API")
    
    def _get_few_shot_examples(self) -> List[Tuple[str, str]]:
        """
        Получает few-shot примеры из базы знаний.
        Ищет примеры вопрос-ответ из релевантных чанков.
        """
        if self.few_shot_examples is not None:
            return self.few_shot_examples
        
        # Примеры вопросов для поиска few-shot примеров
        example_queries = [
            "What is the capital of planet",
            "Who is",
            "What is",
        ]
        
        examples = []
        for query in example_queries:
            # Генерируем эмбеддинг для запроса
            query_embedding = self.embedding_model.encode(
                query, convert_to_numpy=False
            ).tolist()
            
            # Ищем релевантные чанки
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=1
            )
            
            if results["documents"] and len(results["documents"][0]) > 0:
                doc = results["documents"][0][0]
                metadata = results["metadatas"][0][0]
                
                # Формируем вопрос на основе найденного чанка
                title = metadata.get("title", "Unknown")
                # Создаем простой вопрос-ответ пример
                question = f"What is {title}?"
                # Берем первые 200 символов как ответ
                answer = doc[:200].strip() + "..."
                
                examples.append((question, answer))
                
                if len(examples) >= 2:
                    break
        
        # Если не нашли примеры, используем статические
        if len(examples) < 2:
            examples = [
                ("What is the Force?", "The Force is a mystical energy field that binds the galaxy together."),
                ("Who is Luke Skywalker?", "Luke Skywalker is a Jedi Knight and the son of Anakin Skywalker.")
            ]
        
        self.few_shot_examples = examples
        return examples
    
    def search(self, query: str, top_k: int = TOP_K) -> List[Dict]:
        """
        Выполняет поиск релевантных чанков в векторной базе.
        
        Args:
            query: Текстовый запрос пользователя
            top_k: Количество результатов
            
        Returns:
            Список словарей с найденными чанками и метаданными
        """
        # Генерируем эмбеддинг для запроса
        query_embedding = self.embedding_model.encode(
            query, convert_to_numpy=False
        ).tolist()
        
        # Выполняем поиск
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k
        )
        
        # Форматируем результаты
        chunks = []
        if results["ids"] and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                distance = results["distances"][0][i] if "distances" in results else None
                
                # Проверяем релевантность
                if distance is not None and distance > RELEVANCE_THRESHOLD:
                    continue
                
                chunk = {
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": distance
                }
                chunks.append(chunk)
        
        return chunks
    
    def _build_prompt(self, query: str, chunks: List[Dict]) -> str:
        """
        Формирует промпт с контекстом, Few-shot примерами и Chain-of-Thought инструкциями.
        
        Args:
            query: Запрос пользователя
            chunks: Найденные релевантные чанки
            
        Returns:
            Сформированный промпт
        """
        # System промпт с Chain-of-Thought инструкциями
        system_prompt = """Ты помощник, который отвечает на вопросы на основе предоставленной информации из базы знаний о вселенной Star Wars.

ВАЖНО: Всегда следуй этим шагам:
1. Сначала проанализируй запрос пользователя
2. Изучи предоставленные фрагменты информации
3. Найди релевантную информацию в фрагментах
4. Объясни свои шаги рассуждения
5. Дай четкий ответ на основе найденной информации

Если информации недостаточно для ответа, честно скажи "Я не знаю" или "В предоставленной информации нет ответа на этот вопрос"."""
        
        # Получаем few-shot примеры
        few_shot_examples = self._get_few_shot_examples()
        
        # Формируем few-shot секцию
        few_shot_section = "Примеры вопросов и ответов:\n\n"
        for q, a in few_shot_examples:
            few_shot_section += f"Q: {q}\nA: {a}\n\n"
        
        # Формируем контекст из найденных чанков
        context_section = "Контекст из базы знаний:\n\n"
        for i, chunk in enumerate(chunks, 1):
            context_section += f"[Фрагмент {i}]\n"
            context_section += f"Источник: {chunk['metadata'].get('title', 'Unknown')}\n"
            context_section += f"{chunk['text']}\n\n"
        
        # Формируем финальный промпт
        prompt = f"""{system_prompt}

{few_shot_section}

{context_section}

Теперь ответь на вопрос пользователя, следуя шагам выше:

Q: {query}
A:"""
        
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """
        Вызывает YandexGPT для генерации ответа.
        
        Args:
            prompt: Сформированный промпт
            
        Returns:
            Ответ от LLM
        """
        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        headers = {
            "Authorization": f"Api-Key {self.yandex_api_key}",
            "x-folder-id": self.yandex_folder_id,
            "Content-Type": "application/json"
        }
        data = {
            "modelUri": f"gpt://{self.yandex_folder_id}/{YANDEX_MODEL}",
            "completionOptions": {
                "stream": False,
                "temperature": YANDEX_TEMPERATURE,
                "maxTokens": YANDEX_MAX_TOKENS
            },
            "messages": [
                {
                    "role": "user",
                    "text": prompt
                }
            ]
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        # Детальная обработка ошибок
        if response.status_code != 200:
            error_detail = ""
            try:
                error_json = response.json()
                error_detail = f"Детали ошибки: {json.dumps(error_json, indent=2, ensure_ascii=False)}"
            except:
                error_detail = f"Ответ сервера: {response.text}"
            
            raise requests.exceptions.HTTPError(
                f"{response.status_code} {response.reason}: {error_detail}\n"
                f"URL: {url}\n"
                f"Проверьте правильность YANDEX_API_KEY и YANDEX_FOLDER_ID"
            )
        
        response.raise_for_status()
        result = response.json()
        return result["result"]["alternatives"][0]["message"]["text"].strip()
    
    def query(self, user_query: str, top_k: int = TOP_K) -> Dict:
        """
        Основной метод для обработки запроса пользователя.
        
        Args:
            user_query: Запрос пользователя
            top_k: Количество релевантных чанков для поиска
            
        Returns:
            Словарь с ответом и метаданными
        """
        # Поиск релевантных чанков
        chunks = self.search(user_query, top_k=top_k)
        
        # Проверяем, есть ли релевантная информация
        if not chunks:
            return {
                "answer": "Я не знаю. В базе знаний не найдено релевантной информации для ответа на ваш вопрос.",
                "chunks": [],
                "reasoning": "Не найдено релевантных чанков в векторной базе данных."
            }
        
        # Формируем промпт
        prompt = self._build_prompt(user_query, chunks)
        
        # Генерируем ответ через LLM
        try:
            answer = self._call_llm(prompt)
        except Exception as e:
            return {
                "answer": f"Произошла ошибка при генерации ответа: {str(e)}",
                "chunks": chunks,
                "reasoning": f"Ошибка LLM: {str(e)}"
            }
        
        return {
            "answer": answer,
            "chunks": chunks,
            "reasoning": f"Найдено {len(chunks)} релевантных фрагментов из базы знаний."
        }

