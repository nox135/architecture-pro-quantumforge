"""
Скрипт для тестирования RAG-бота напрямую (без API).
"""

from rag_engine import RAGEngine


def test_rag():
    """Тестирование RAG-бота на примерах."""
    print("=" * 80)
    print("Тестирование RAG-бота")
    print("=" * 80)
    print()
    
    try:
        # Инициализация RAG-движка
        print("Инициализация RAG-движка...")
        rag = RAGEngine()
        print("RAG-движок готов")
        print()
        
        # Тестовые запросы
        test_queries = [
            "What is the Force?",
            "Who is Luke Skywalker?",
            "What is a lightsaber?",
            "Tell me about Darth Vader",
            "What is the Death Star?",
            "How to cook borscht?",  # Вопрос вне предметной области
        ]
        
        for i, query in enumerate(test_queries, 1):
            print("=" * 80)
            print(f"Запрос #{i}: {query}")
            print("=" * 80)
            print()
            
            try:
                result = rag.query(query, top_k=3)
                
                print("Ответ:")
                print(result["answer"])
                print()
                print(f"Обоснование: {result['reasoning']}")
                print(f"Найдено релевантных чанков: {len(result['chunks'])}")
                print()
                
                if result["chunks"]:
                    print("Использованные источники:")
                    for j, chunk in enumerate(result["chunks"], 1):
                        print(f"  {j}. {chunk['metadata'].get('title', 'Unknown')}")
                        if chunk.get('distance') is not None:
                            print(f"     Расстояние: {chunk['distance']:.4f}")
                print()
                
            except Exception as e:
                print(f"Ошибка при обработке запроса: {e}")
                print()
        
        print("=" * 80)
        print("Тестирование завершено")
        print("=" * 80)
        
    except Exception as e:
        print(f"Ошибка при инициализации: {e}")
        print("\nУбедитесь, что:")
        print("1. Векторный индекс создан (Task3/build_index.py)")
        print("2. Установлены переменные окружения YANDEX_API_KEY и YANDEX_FOLDER_ID")


if __name__ == "__main__":
    test_rag()



