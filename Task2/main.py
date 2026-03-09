"""
Главный скрипт, который запускает все этапы обработки:
1. Скачивание HTML-страниц
2. Очистка текстов
3. Замена терминов
"""

import os
import sys

def run_script(script_name: str):
    """Запускает Python-скрипт и обрабатывает ошибки."""
    print(f"\n{'='*60}")
    print(f"Запуск: {script_name}")
    print(f"{'='*60}\n")
    
    try:
        with open(script_name, "r", encoding="utf-8") as f:
            code = f.read()
        exec(compile(code, script_name, "exec"), {"__name__": "__main__"})
        return True
    except Exception as e:
        print(f"\n✗ Ошибка при выполнении {script_name}: {e}")
        return False


def main():
    """Запускает все этапы обработки последовательно."""
    scripts = [
        "01_download_pages.py",
        "02_clean_texts.py",
        "03_replace_terms.py"
    ]
    
    print("="*60)
    print("Создание базы знаний для RAG")
    print("="*60)
    
    for script in scripts:
        if not os.path.exists(script):
            print(f"\n✗ Файл {script} не найден!")
            sys.exit(1)
        
        success = run_script(script)
        if not success:
            print(f"\n✗ Процесс остановлен из-за ошибки в {script}")
            sys.exit(1)
    
    print("\n" + "="*60)
    print("✓ Все этапы выполнены успешно!")
    print("="*60)
    print(f"\nРезультаты сохранены в папку: knowledge_base/")
    print(f"Словарь замен: knowledge_base/terms_map.json")


if __name__ == "__main__":
    main()

