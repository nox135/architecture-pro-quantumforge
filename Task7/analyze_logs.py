"""
Скрипт для анализа логов запросов к RAG-боту.
Выявляет пробелы в базе знаний и проблемы с качеством ответов.
"""

import json
from pathlib import Path
from collections import defaultdict
from typing import List, Dict
from datetime import datetime


def load_logs(log_file: Path) -> List[Dict]:
    """
    Загружает логи из JSONL файла.
    
    Args:
        log_file: Путь к файлу лога
        
    Returns:
        Список записей лога
    """
    logs = []
    
    if not log_file.exists():
        print(f"Ошибка: Файл {log_file} не найден")
        return logs
    
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    log_entry = json.loads(line)
                    logs.append(log_entry)
                except json.JSONDecodeError:
                    continue
    
    return logs


def analyze_logs(logs: List[Dict]) -> Dict:
    """
    Анализирует логи и выявляет проблемы.
    
    Args:
        logs: Список записей лога
        
    Returns:
        Словарь с результатами анализа
    """
    if not logs:
        return {"error": "Нет данных для анализа"}
    
    # Базовая статистика
    total_queries = len(logs)
    successful_queries = sum(1 for log in logs if log.get("success", False))
    failed_queries = total_queries - successful_queries
    
    # Анализ по категориям
    failed_by_category = defaultdict(int)
    failed_queries_list = []
    
    for log in logs:
        if not log.get("success", False):
            # Пытаемся определить категорию из запроса
            query = log.get("query", "").lower()
            category = "unknown"
            
            if any(word in query for word in ["кто", "who"]):
                category = "персонаж"
            elif any(word in query for word in ["что", "what", "как", "how"]):
                category = "концепт/технология"
            elif any(word in query for word in ["где", "where", "планета", "planet"]):
                category = "планета"
            
            failed_by_category[category] += 1
            failed_queries_list.append({
                "query": log.get("query"),
                "answer": log.get("answer", "")[:100] + "..." if len(log.get("answer", "")) > 100 else log.get("answer", ""),
                "chunks_found": log.get("chunks_found", False),
                "chunks_count": log.get("chunks_count", 0),
                "category": category
            })
    
    # Анализ источников
    all_sources = []
    for log in logs:
        sources = log.get("sources", [])
        for source in sources:
            all_sources.append(source.get("title", "Unknown"))
    
    source_usage = defaultdict(int)
    for source in all_sources:
        source_usage[source] += 1
    
    # Проблемы с релевантностью
    irrelevant_sources = []
    for log in logs:
        if not log.get("success", False) and log.get("chunks_found", False):
            # Найдены чанки, но ответ неуспешен - возможно, нерелевантные источники
            sources = log.get("sources", [])
            irrelevant_sources.append({
                "query": log.get("query"),
                "sources": [s.get("title", "Unknown") for s in sources]
            })
    
    # Статистика по длине ответов
    answer_lengths = [log.get("answer_length", 0) for log in logs]
    avg_answer_length = sum(answer_lengths) / len(answer_lengths) if answer_lengths else 0
    
    # Анализ результатов
    analysis = {
        "summary": {
            "total_queries": total_queries,
            "successful_queries": successful_queries,
            "failed_queries": failed_queries,
            "success_rate": (successful_queries / total_queries * 100) if total_queries > 0 else 0,
            "average_answer_length": round(avg_answer_length, 2)
        },
        "failed_by_category": dict(failed_by_category),
        "failed_queries": failed_queries_list[:10],  # Первые 10 для примера
        "top_sources": dict(sorted(source_usage.items(), key=lambda x: x[1], reverse=True)[:10]),
        "irrelevant_sources_count": len(irrelevant_sources),
        "irrelevant_sources_examples": irrelevant_sources[:5]
    }
    
    return analysis


def generate_report(analysis: Dict, output_file: Path):
    """
    Генерирует текстовый отчет на основе анализа.
    
    Args:
        analysis: Результаты анализа
        output_file: Путь к файлу отчета
    """
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("ОТЧЕТ ПО АНАЛИЗУ ЛОГОВ RAG-БОТА\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Дата анализа: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Общая статистика
        summary = analysis.get("summary", {})
        f.write("ОБЩАЯ СТАТИСТИКА\n")
        f.write("-" * 60 + "\n")
        f.write(f"Всего запросов: {summary.get('total_queries', 0)}\n")
        f.write(f"Успешных ответов: {summary.get('successful_queries', 0)}\n")
        f.write(f"Неуспешных ответов: {summary.get('failed_queries', 0)}\n")
        f.write(f"Процент успешности: {summary.get('success_rate', 0):.2f}%\n")
        f.write(f"Средняя длина ответа: {summary.get('average_answer_length', 0):.0f} символов\n\n")
        
        # Пробелы по категориям
        failed_by_category = analysis.get("failed_by_category", {})
        if failed_by_category:
            f.write("ПРОБЕЛЫ ПО КАТЕГОРИЯМ\n")
            f.write("-" * 60 + "\n")
            for category, count in sorted(failed_by_category.items(), key=lambda x: x[1], reverse=True):
                f.write(f"{category}: {count} неуспешных запросов\n")
            f.write("\n")
        
        # Примеры неуспешных запросов
        failed_queries = analysis.get("failed_queries", [])
        if failed_queries:
            f.write("ПРИМЕРЫ НЕУСПЕШНЫХ ЗАПРОСОВ\n")
            f.write("-" * 60 + "\n")
            for i, query_info in enumerate(failed_queries[:5], 1):
                f.write(f"{i}. Вопрос: {query_info.get('query')}\n")
                f.write(f"   Категория: {query_info.get('category')}\n")
                f.write(f"   Найдено чанков: {query_info.get('chunks_count', 0)}\n")
                f.write(f"   Ответ: {query_info.get('answer', '')[:150]}...\n\n")
        
        # Нерелевантные источники
        irrelevant_count = analysis.get("irrelevant_sources_count", 0)
        if irrelevant_count > 0:
            f.write("ПРОБЛЕМЫ С РЕЛЕВАНТНОСТЬЮ\n")
            f.write("-" * 60 + "\n")
            f.write(f"Найдено случаев с нерелевантными источниками: {irrelevant_count}\n")
            examples = analysis.get("irrelevant_sources_examples", [])
            for i, example in enumerate(examples[:3], 1):
                f.write(f"\nПример {i}:\n")
                f.write(f"  Вопрос: {example.get('query')}\n")
                f.write(f"  Источники: {', '.join(example.get('sources', []))}\n")
            f.write("\n")
        
        # Рекомендации
        f.write("РЕКОМЕНДАЦИИ ПО УЛУЧШЕНИЮ\n")
        f.write("-" * 60 + "\n")
        
        if summary.get("success_rate", 0) < 70:
            f.write("1. КРИТИЧНО: Процент успешности ниже 70%. Необходимо:\n")
            f.write("   - Расширить базу знаний по темам с высоким процентом неуспешных запросов\n")
            f.write("   - Проверить качество индексации документов\n")
            f.write("   - Улучшить алгоритм поиска релевантных чанков\n\n")
        
        if failed_by_category:
            top_category = max(failed_by_category.items(), key=lambda x: x[1])
            f.write(f"2. Расширить базу знаний по категории '{top_category[0]}':\n")
            f.write(f"   - Найдено {top_category[1]} неуспешных запросов в этой категории\n\n")
        
        if irrelevant_count > 0:
            f.write("3. Улучшить релевантность поиска:\n")
            f.write("   - Настроить порог релевантности (RELEVANCE_THRESHOLD)\n")
            f.write("   - Улучшить качество эмбеддингов\n")
            f.write("   - Добавить фильтрацию по метаданным\n\n")
        
        f.write("4. Общие рекомендации:\n")
        f.write("   - Регулярно обновлять базу знаний\n")
        f.write("   - Проводить автоматическое тестирование на золотом наборе вопросов\n")
        f.write("   - Мониторить логи для выявления новых пробелов\n")
        f.write("   - Улучшать промпты для LLM для более точных ответов\n")


def main():
    """
    Основная функция для анализа логов.
    """
    script_dir = Path(__file__).parent.absolute()
    log_file = script_dir / "logs.jsonl"
    
    print("=" * 60)
    print("Анализ логов RAG-бота")
    print("=" * 60)
    
    # Загрузка логов
    print(f"\nЗагрузка логов из {log_file}...")
    logs = load_logs(log_file)
    
    if not logs:
        print("Ошибка: Не найдено записей в логе")
        return
    
    print(f"Загружено записей: {len(logs)}")
    
    # Анализ
    print("\nВыполнение анализа...")
    analysis = analyze_logs(logs)
    
    # Сохранение результатов анализа
    analysis_file = script_dir / "analysis.json"
    with open(analysis_file, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    print(f"Результаты анализа сохранены в {analysis_file}")
    
    # Генерация отчета
    report_file = script_dir / "analysis_report.txt"
    print(f"\nГенерация отчета...")
    generate_report(analysis, report_file)
    
    print(f"Отчет сохранен в {report_file}")
    
    # Вывод краткой статистики
    summary = analysis.get("summary", {})
    print("\n" + "=" * 60)
    print("КРАТКАЯ СТАТИСТИКА")
    print("=" * 60)
    print(f"Всего запросов: {summary.get('total_queries', 0)}")
    print(f"Успешных: {summary.get('successful_queries', 0)}")
    print(f"Неуспешных: {summary.get('failed_queries', 0)}")
    print(f"Процент успешности: {summary.get('success_rate', 0):.2f}%")
    
    failed_by_category = analysis.get("failed_by_category", {})
    if failed_by_category:
        print("\nПробелы по категориям:")
        for category, count in sorted(failed_by_category.items(), key=lambda x: x[1], reverse=True):
            print(f"  {category}: {count}")


if __name__ == "__main__":
    main()

