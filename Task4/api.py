"""
REST API для RAG-бота на FastAPI.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

from rag_engine import RAGEngine
from config import API_HOST, API_PORT


# Модели данных
class QueryRequest(BaseModel):
    """Модель запроса."""
    query: str
    top_k: Optional[int] = 3


class QueryResponse(BaseModel):
    """Модель ответа."""
    answer: str
    reasoning: str
    chunks_count: int
    chunks: list


# Глобальный экземпляр RAG-движка
rag_engine: Optional[RAGEngine] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения."""
    # Startup
    global rag_engine
    try:
        rag_engine = RAGEngine()
        print("RAG-движок успешно инициализирован")
    except Exception as e:
        print(f"Ошибка при инициализации RAG-движка: {e}")
        raise
    yield
    # Shutdown (если нужно что-то очистить)


# Инициализация FastAPI приложения
app = FastAPI(
    title="RAG Bot API",
    description="REST API для RAG-бота с Few-shot и Chain-of-Thought",
    version="1.0.0",
    lifespan=lifespan
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Корневой эндпоинт."""
    return {
        "message": "RAG Bot API",
        "version": "1.0.0",
        "endpoints": {
            "query": "/query",
            "health": "/health"
        }
    }


@app.get("/health")
async def health():
    """Проверка здоровья сервиса."""
    if rag_engine is None:
        raise HTTPException(status_code=503, detail="RAG engine not initialized")
    
    return {
        "status": "healthy",
        "engine_loaded": rag_engine is not None
    }


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Обработка запроса пользователя через RAG-движок.
    
    Args:
        request: Запрос с текстом вопроса
        
    Returns:
        Ответ с результатом поиска и генерации
    """
    if rag_engine is None:
        raise HTTPException(status_code=503, detail="RAG engine not initialized")
    
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        # Обрабатываем запрос
        result = rag_engine.query(request.query, top_k=request.top_k)
        
        # Формируем ответ
        response = QueryResponse(
            answer=result["answer"],
            reasoning=result["reasoning"],
            chunks_count=len(result["chunks"]),
            chunks=[
                {
                    "text": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"],
                    "source": chunk["metadata"].get("title", "Unknown"),
                    "distance": chunk.get("distance")
                }
                for chunk in result["chunks"]
            ]
        )
        
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


if __name__ == "__main__":
    print(f"Запуск сервера на {API_HOST}:{API_PORT}")
    try:
        uvicorn.run(app, host=API_HOST, port=API_PORT)
    except OSError as e:
        if "10048" in str(e) or "address already in use" in str(e).lower():
            print(f"\n✗ Ошибка: Порт {API_PORT} уже занят!")
            print(f"   Решения:")
            print(f"   1. Остановите другой процесс, использующий порт {API_PORT}")
            print(f"   2. Или измените порт через переменную окружения: $env:API_PORT=\"8001\"")
            print(f"   3. Или добавьте в .env файл: API_PORT=8001")
        else:
            raise



