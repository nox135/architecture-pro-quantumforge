"""
Скрипт для замены ключевых терминов на вымышленные названия.
Использует словарь замен из terms_map.json.
"""

import os
import json
from tqdm import tqdm
import re

INPUT_DIR = "cleaned_texts"
OUTPUT_DIR = "knowledge_base"
TERMS_MAP_FILE = "terms_map.json"


def load_terms_map() -> dict:
    """Загружает словарь замен из JSON-файла."""
    with open(TERMS_MAP_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["replacements"]


def create_replacement_patterns(terms_map: dict) -> list:
    """
    Создает список паттернов для замены.
    Сортирует по длине (от длинных к коротким), чтобы избежать конфликтов.
    """
    patterns = []
    for original, replacement in terms_map.items():
        # Экранируем специальные символы regex
        escaped_original = re.escape(original)
        # Заменяем с учетом границ слов для точного совпадения
        pattern = (rf"\b{escaped_original}\b", replacement)
        patterns.append(pattern)
    
    # Сортируем по длине (от длинных к коротким)
    patterns.sort(key=lambda x: len(x[0]), reverse=True)
    return patterns


def replace_terms_in_text(text: str, patterns: list) -> str:
    """Заменяет все термины в тексте согласно словарю."""
    result = text
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result


def process_text_file(txt_file: str, patterns: list) -> str:
    """Обрабатывает один текстовый файл и возвращает текст с замененными терминами."""
    filepath = os.path.join(INPUT_DIR, txt_file)
    
    if not os.path.exists(filepath):
        return None
    
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    
    replaced_text = replace_terms_in_text(text, patterns)
    return replaced_text


def save_replaced_text(page_name: str, text: str):
    """Сохраняет текст с замененными терминами в папку knowledge_base."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Убираем расширение .txt если есть
    base_name = page_name.replace(".txt", "")
    filepath = os.path.join(OUTPUT_DIR, f"{base_name}.txt")
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(text)
    
    return filepath


def main():
    """Основная функция для замены терминов во всех текстовых файлах."""
    if not os.path.exists(INPUT_DIR):
        print(f"Ошибка: папка {INPUT_DIR} не найдена!")
        print("Сначала запустите скрипт 02_clean_texts.py")
        return
    
    if not os.path.exists(TERMS_MAP_FILE):
        print(f"Ошибка: файл {TERMS_MAP_FILE} не найден!")
        return
    
    txt_files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".txt")]
    
    if not txt_files:
        print(f"Ошибка: в папке {INPUT_DIR} нет текстовых файлов!")
        return
    
    print("Загружаю словарь замен...")
    terms_map = load_terms_map()
    patterns = create_replacement_patterns(terms_map)
    print(f"Загружено {len(terms_map)} замен\n")
    
    print(f"Начинаю замену терминов в {len(txt_files)} файлах...\n")
    
    processed = 0
    failed = []
    
    for txt_file in tqdm(txt_files, desc="Замена терминов"):
        replaced_text = process_text_file(txt_file, patterns)
        
        if replaced_text and len(replaced_text) > 100:
            page_name = txt_file.replace(".txt", "")
            save_replaced_text(page_name, replaced_text)
            processed += 1
        else:
            failed.append(txt_file)
    
    print(f"\n✓ Обработано успешно: {processed}/{len(txt_files)}")
    if failed:
        print(f"✗ Проблемы с файлами: {', '.join(failed)}")
    
    print(f"\nФинальные документы сохранены в папку: {OUTPUT_DIR}/")
    
    # Копируем terms_map.json в knowledge_base
    import shutil
    shutil.copy(TERMS_MAP_FILE, os.path.join(OUTPUT_DIR, TERMS_MAP_FILE))
    print(f"Словарь замен скопирован в {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()

