"""
Скрипт для очистки HTML и извлечения чистого текста.
Сохраняет тексты в отдельных файлах (один файл = одна сущность).
"""

import os
from bs4 import BeautifulSoup
from tqdm import tqdm
import re

INPUT_DIR = "raw_html"
OUTPUT_DIR = "cleaned_texts"


def clean_text(html_content: str) -> str:
    """Извлекает и очищает текст из HTML."""
    soup = BeautifulSoup(html_content, "lxml")
    
    # Удаляем ненужные элементы
    for element in soup.find_all(["script", "style", "nav", "footer", "header", "aside"]):
        element.decompose()
    
    # Находим основной контент статьи
    main_content = soup.find("div", class_="mw-parser-output")
    if not main_content:
        main_content = soup.find("main") or soup.find("article") or soup.find("body")
    
    if not main_content:
        return ""
    
    # Извлекаем текст
    text = main_content.get_text(separator="\n", strip=True)
    
    # Очищаем от лишних пробелов и переносов
    text = re.sub(r"\n{3,}", "\n\n", text)  # Убираем множественные переносы
    text = re.sub(r"[ \t]+", " ", text)  # Убираем множественные пробелы
    text = text.strip()
    
    return text


def process_html_file(html_file: str) -> str:
    """Обрабатывает один HTML-файл и возвращает очищенный текст."""
    filepath = os.path.join(INPUT_DIR, html_file)
    
    if not os.path.exists(filepath):
        return None
    
    with open(filepath, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    cleaned_text = clean_text(html_content)
    return cleaned_text


def save_cleaned_text(page_name: str, text: str):
    """Сохраняет очищенный текст в файл."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Убираем расширение .html если есть
    base_name = page_name.replace(".html", "")
    filepath = os.path.join(OUTPUT_DIR, f"{base_name}.txt")
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(text)
    
    return filepath


def main():
    """Основная функция для очистки всех HTML-файлов."""
    if not os.path.exists(INPUT_DIR):
        print(f"Ошибка: папка {INPUT_DIR} не найдена!")
        print("Сначала запустите скрипт 01_download_pages.py")
        return
    
    html_files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".html")]
    
    if not html_files:
        print(f"Ошибка: в папке {INPUT_DIR} нет HTML-файлов!")
        return
    
    print(f"Начинаю очистку текстов из {len(html_files)} HTML-файлов...\n")
    
    processed = 0
    failed = []
    
    for html_file in tqdm(html_files, desc="Очистка"):
        cleaned_text = process_html_file(html_file)
        
        if cleaned_text and len(cleaned_text) > 100:  # Минимум 100 символов
            page_name = html_file.replace(".html", "")
            save_cleaned_text(page_name, cleaned_text)
            processed += 1
        else:
            failed.append(html_file)
    
    print(f"\n✓ Обработано успешно: {processed}/{len(html_files)}")
    if failed:
        print(f"✗ Проблемы с файлами: {', '.join(failed)}")
    
    print(f"\nОчищенные тексты сохранены в папку: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()

