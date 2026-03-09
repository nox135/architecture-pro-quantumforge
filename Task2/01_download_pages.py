"""
Скрипт для скачивания HTML-страниц с Star Wars Fandom.
Сохраняет исходные HTML-файлы для последующей обработки.
"""

import os
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import time

# Список ключевых страниц для скачивания
PAGES = [
    "Darth_Vader",
    "Luke_Skywalker",
    "Princess_Leia",
    "Han_Solo",
    "Obi-Wan_Kenobi",
    "Yoda",
    "Emperor_Palpatine",
    "Anakin_Skywalker",
    "Death_Star",
    "The_Force",
    "Jedi",
    "Sith",
    "Lightsaber",
    "Stormtrooper",
    "Rebel_Alliance",
    "Galactic_Empire",
    "Tatooine",
    "Coruscant",
    "Alderaan",
    "Hoth",
    "Dagobah",
    "Endor",
    "Millennium_Falcon",
    "X-wing",
    "TIE_Fighter",
    "R2-D2",
    "C-3PO",
    "Chewbacca",
    "Wookiee",
    "Ewok",
    "Droid",
    "Clone_Trooper",
    "Mandalorian",
    "Boba_Fett",
    "Darth_Maul",
    "Count_Dooku",
    "General_Grievous",
    "Padmé_Amidala",
    "Mace_Windu",
    "Qui-Gon_Jinn"
]

BASE_URL = "https://starwars.fandom.com/wiki/"
OUTPUT_DIR = "raw_html"
DELAY = 2  # Задержка между запросами в секундах


def download_page(page_name: str) -> str:
    """Скачивает HTML-страницу и возвращает её содержимое."""
    url = BASE_URL + page_name
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Ошибка при скачивании {page_name}: {e}")
        return None


def save_html(page_name: str, html_content: str):
    """Сохраняет HTML-контент в файл."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, f"{page_name}.html")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)
    return filepath


def main():
    """Основная функция для скачивания всех страниц."""
    print("Начинаю скачивание страниц с Star Wars Fandom...")
    print(f"Всего страниц: {len(PAGES)}\n")
    
    downloaded = 0
    failed = []
    
    for page_name in tqdm(PAGES, desc="Скачивание"):
        html_content = download_page(page_name)
        
        if html_content:
            save_html(page_name, html_content)
            downloaded += 1
        else:
            failed.append(page_name)
        
        # Задержка между запросами, чтобы не перегружать сервер
        time.sleep(DELAY)
    
    print(f"\n✓ Скачано успешно: {downloaded}/{len(PAGES)}")
    if failed:
        print(f"✗ Ошибки при скачивании: {', '.join(failed)}")
    
    print(f"\nHTML-файлы сохранены в папку: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()

