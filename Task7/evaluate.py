"""
Скрипт автоматического тестирования RAG-бота на золотом наборе вопросов.
Оценивает качество ответов и сохраняет результаты в лог.
"""

import sys
from pathlib import Path
import json
from typing import List, Dict

# Добавляем пути для импорта
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT / "Task4"))
sys.path.insert(0, str(SCRIPT_DIR))  # Для импорта logger из текущей директории

from rag_engine import RAGEngine
from logger import RAGLogger


def load_golden_questions(questions_file: Path) -> List[Dict]:
    """
    Загружает золотой набор вопросов из файла.
    
    Args:
        questions_file: Путь к файлу с вопросами
        
    Returns:
        Список словарей с вопросами и метаданными
    """
    questions = []
    
    if not questions_file.exists():
        print(f"Ошибка: Файл {questions_file} не найден")
        return questions
    
    with open(questions_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Пропускаем комментарии и пустые строки
            if not line or line.startswith("#"):
                continue
            
            # Парсим строку: вопрос | ожидаемый_ответ | категория | должен_ответить
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 4:
                question = parts[0]
                expected_answer = parts[1]
                category = parts[2]
                should_answer = parts[3].lower() == "да"
                
                questions.append({
                    "question": question,
                    "expected_answer": expected_answer,
                    "category": category,
                    "should_answer": should_answer
                })
    
    return questions


def evaluate_answer(
    question: str,
    answer: str,
    chunks: List[Dict],
    should_answer: bool
) -> Dict:
    """
    Оценивает качество ответа на вопрос.
    
    Args:
        question: Вопрос пользователя
        answer: Ответ бота
        chunks: Найденные чанки
        should_answer: Должен ли бот ответить на этот вопрос
        
    Returns:
        Словарь с оценкой качества
    """
    # Базовые метрики
    chunks_found = len(chunks) > 0
    answer_length = len(answer)
    
    # Определяем, был ли ответ успешным
    failure_indicators = [
        "я не знаю",
        "не найдено",
        "нет информации",
        "не могу ответить",
        "i don't know",
        "not found",
        "no information"
    ]
    
    answer_lower = answer.lower()
    has_failure_indicator = any(indicator in answer_lower for indicator in failure_indicators)
    
    # Оценка корректности
    if should_answer:
        # Бот должен был ответить
        is_correct = chunks_found and not has_failure_indicator and answer_length >= 20
    else:
        # Бот не должен был ответить (тема удалена)
        is_correct = not chunks_found or has_failure_indicator or answer_length < 50
    
    # Дополнительные метрики
    evaluation = {
        "chunks_found": chunks_found,
        "chunks_count": len(chunks),
        "answer_length": answer_length,
        "has_failure_indicator": has_failure_indicator,
        "is_correct": is_correct,
        "should_answer": should_answer
    }
    
    return evaluation


def run_evaluation():
    """
    Запускает автоматическое тестирование на золотом наборе вопросов.
    """
    print("=" * 60)
    print("Автоматическое тестирование RAG-бота")
    print("=" * 60)
    
    # Инициализация RAG-движка
    print("\nИнициализация RAG-движка...")
    try:
        rag_engine = RAGEngine()
    except Exception as e:
        print(f"Ошибка при инициализации RAG-движка: {e}")
        return
    
    # Инициализация логгера
    logger = RAGLogger()
    
    # Загрузка золотых вопросов
    questions_file = SCRIPT_DIR / "golden_questions.txt"
    print(f"\nЗагрузка золотых вопросов из {questions_file}...")
    questions = load_golden_questions(questions_file)
    
    if not questions:
        print("Ошибка: Не удалось загрузить вопросы")
        return
    
    print(f"Загружено вопросов: {len(questions)}")
    
    # Очищаем предыдущий лог
    logger.clear_logs()
    
    # Результаты тестирования
    results = {
        "total_questions": len(questions),
        "correct_answers": 0,
        "incorrect_answers": 0,
        "questions": []
    }
    
    # Тестирование каждого вопроса
    print("\n" + "=" * 60)
    print("Начало тестирования")
    print("=" * 60)
    
    for i, question_data in enumerate(questions, 1):
        question = question_data["question"]
        should_answer = question_data["should_answer"]
        
        print(f"\n[{i}/{len(questions)}] Вопрос: {question}")
        print(f"  Ожидается ответ: {'Да' if should_answer else 'Нет'}")
        
        # Выполняем запрос
        try:
            response = rag_engine.query(question)
            answer = response["answer"]
            chunks = response["chunks"]
            reasoning = response["reasoning"]
        except Exception as e:
            print(f"  Ошибка при выполнении запроса: {e}")
            answer = f"Ошибка: {str(e)}"
            chunks = []
            reasoning = "Ошибка при выполнении запроса"
        
        # Оцениваем ответ
        evaluation = evaluate_answer(question, answer, chunks, should_answer)
        
        # Логируем запрос
        log_entry = logger.log_query(
            query=question,
            answer=answer,
            chunks=chunks,
            reasoning=reasoning,
            success=evaluation["is_correct"],
            answer_length=evaluation["answer_length"]
        )
        
        # Сохраняем результат
        question_result = {
            "question": question,
            "category": question_data["category"],
            "expected_answer": question_data["expected_answer"],
            "should_answer": should_answer,
            "actual_answer": answer[:200] + "..." if len(answer) > 200 else answer,
            "evaluation": evaluation
        }
        results["questions"].append(question_result)
        
        # Обновляем статистику
        if evaluation["is_correct"]:
            results["correct_answers"] += 1
            print(f"  ✓ Ответ корректен")
        else:
            results["incorrect_answers"] += 1
            print(f"  ✗ Ответ некорректен")
            print(f"    Найдено чанков: {evaluation['chunks_count']}")
            print(f"    Длина ответа: {evaluation['answer_length']}")
    
    # Итоговая статистика
    accuracy = (results["correct_answers"] / results["total_questions"]) * 100
    
    print("\n" + "=" * 60)
    print("Результаты тестирования")
    print("=" * 60)
    print(f"Всего вопросов: {results['total_questions']}")
    print(f"Правильных ответов: {results['correct_answers']}")
    print(f"Неправильных ответов: {results['incorrect_answers']}")
    print(f"Точность: {accuracy:.2f}%")
    
    # Сохраняем результаты
    results_file = SCRIPT_DIR / "evaluation_results.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nРезультаты сохранены в {results_file}")
    print(f"Логи сохранены в {logger.log_file}")
    
    return results


if __name__ == "__main__":
    run_evaluation()

