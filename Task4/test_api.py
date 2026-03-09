"""
Скрипт для тестирования RAG-бота через REST API.
"""

import requests
import json
from config import API_PORT


def test_api():
    """Тестирование RAG-бота через API."""
    base_url = f"http://localhost:{API_PORT}"
    
    # Проверка здоровья сервиса
    print("Проверка здоровья сервиса...")
    try:
        response = requests.get(f"{base_url}/health")
        response.raise_for_status()
        print(f"✓ Сервис работает: {response.json()}")
    except Exception as e:
        print(f"✗ Ошибка подключения к сервису: {e}")
        print("Убедитесь, что API сервер запущен: python api.py")
        return
    
    print()
    
    # Тестовые запросы
    test_queries = [
        {"query": "What is the Force? Отвечай на русском", "top_k": 3},
        {"query": "Who is Luke Skywalker? Отвечай на русском", "top_k": 3},
        {"query": "What is a lightsaber? Отвечай на русском", "top_k": 3},
        {"query": "Tell me about Darth Vader Отвечай на русском", "top_k": 3},
        {"query": "How to cook borscht? Отвечай на русском", "top_k": 3},  # Вопрос вне предметной области
    ]
    
    for i, query_data in enumerate(test_queries, 1):
        print("=" * 80)
        print(f"Запрос #{i}: {query_data['query']}")
        print("=" * 80)
        print()
        
        try:
            response = requests.post(
                f"{base_url}/query",
                json=query_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            result = response.json()
            
            print("Ответ:")
            print(result["answer"])
            print()
            print(f"Обоснование: {result['reasoning']}")
            print(f"Найдено релевантных чанков: {result['chunks_count']}")
            print()
            
            if result["chunks"]:
                print("Использованные источники:")
                for j, chunk in enumerate(result["chunks"], 1):
                    print(f"  {j}. {chunk['source']}")
                    if chunk.get('distance') is not None:
                        print(f"     Расстояние: {chunk['distance']:.4f}")
            print()
            
        except requests.exceptions.HTTPError as e:
            print(f"✗ HTTP ошибка: {e}")
            if e.response is not None:
                try:
                    error_detail = e.response.json()
                    print(f"Детали: {json.dumps(error_detail, indent=2, ensure_ascii=False)}")
                except:
                    print(f"Ответ сервера: {e.response.text}")
            print()
        except Exception as e:
            print(f"✗ Ошибка: {e}")
            print()
    
    print("=" * 80)
    print("Тестирование завершено")
    print("=" * 80)


if __name__ == "__main__":
    test_api()

