import sqlite3
import time
import requests
from bs4 import BeautifulSoup

DB_NAME = "ao3_full.db"
BASE_URL = "https://archiveofourown.org/works/search"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fics (
            id TEXT PRIMARY KEY,
            title TEXT,
            author TEXT,
            url TEXT,
            fandoms TEXT,
            summary TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scraper_progress (
            id INTEGER PRIMARY KEY,
            last_page INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def get_last_parsed_page():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT last_page FROM scraper_progress WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 1

def save_parsed_page(page_num):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO scraper_progress (id, last_page)
        VALUES (1, ?)
    ''', (page_num,))
    conn.commit()
    conn.close()

def start_scraping():
    init_db()
    page = get_last_parsed_page()
    
    print("=" * 40)
    print(f"🚀 ЗАПУСК ПАРСЕРА AO3")
    print(f"Починаємо зі сторінки: {page}")
    print("=" * 40)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    while True:
        params = {
            "commit": "Search",
            "work_search[language_id]": "uk",
            "work_search[sort_column]": "created_at",
            "work_search[sort_direction]": "desc",
            "page": page
        }

        try:
            response = requests.get(BASE_URL, headers=headers, params=params)
            
            if response.status_code == 429:
                print("⚠️ AO3 видав 429 (Too Many Requests). Пауза 60 секунд...")
                time.sleep(60)
                continue
            elif response.status_code != 200:
                print(f"Помилка завантаження сторінки {page}: Код {response.status_code}")
                time.sleep(10)
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            works = soup.find_all('li', class_='work')

            if not works:
                print(f"🎉 Більше фанфіків немає! Збір повністю завершено на сторінці {page - 1}.")
                break

            for work in works:
                try:
                    title_tag = work.find('h4', class_='heading')
                    if not title_tag:
                        continue

                    links = title_tag.find_all('a')
                    if not links:
                        continue

                    fic_title_elem = links[0]
                    fic_id = fic_title_elem['href'].split('/')[-1]
                    title = fic_title_elem.text.strip()

                    author = links[1].text.strip() if len(links) > 1 else "Anonymous"

                    fandom_tags = work.find('h5', class_='fandoms')
                    fandoms = ", ".join([f.text.strip() for f in fandom_tags.find_all('a')]) if fandom_tags else "Без фендому"

                    summary_div = work.find('blockquote', class_='summary')
                    summary = summary_div.text.strip() if summary_div else "Без опису"

                    fic_url = f"https://archiveofourown.org/works/{fic_id}"

                    cursor.execute('''
                        INSERT OR REPLACE INTO fics (id, title, author, url, fandoms, summary)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (fic_id, title, author, fic_url, fandoms, summary))

                except Exception as e:
                    continue

            conn.commit()
            save_parsed_page(page)
            
            print(f"✅ Оброблено сторінку {page} (зібрано ~{page * 20} робіт)")

            page += 1
            time.sleep(2.5)

        except Exception as e:
            print(f"Помилка на сторінці {page}: {e}")
            time.sleep(5)

    conn.close()

# Оце той самий виклик, без якого скрипт мовчки завершувався!
start_scraping()
