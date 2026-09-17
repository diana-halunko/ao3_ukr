import sqlite3
import time
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import HTMLResponse

app = FastAPI()

def init_db():
    conn = sqlite3.connect('fics.db', timeout=10)
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
    conn.commit()
    conn.close()

# Ініціалізуємо базу при запуску
init_db()

def fetch_ao3_ukrainian_100():
    """Фоновий збір 100 фанфіків (5 сторінок по 20 робіт)"""
    base_url = "https://archiveofourown.org/works/search"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    conn = sqlite3.connect('fics.db')
    cursor = conn.cursor()

    for page in range(1, 6):
        params = {
            "commit": "Search",
            "work_search[language_id]": "uk",
            "work_search[sort_column]": "created_at",
            "work_search[sort_direction]": "desc",
            "page": page
        }

        try:
            response = requests.get(base_url, headers=headers, params=params)
            if response.status_code != 200:
                print(f"Помилка завантаження сторінки {page}: Status {response.status_code}")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            works = soup.find_all('li', class_='work')

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
                    print(f"Помилка елемента: {e}")
                    continue

            conn.commit()
            print(f"Сторінка {page} з 5 успішно збережена в fics.db!")
            time.sleep(3) # Вежлива затримка між запитами

        except Exception as e:
            print(f"Помилка мережі на сторінці {page}: {e}")

    conn.close()
    print("Парсинг 100 робіт успішно завершено!")

@app.get("/", response_class=HTMLResponse)
def read_root():
    conn = sqlite3.connect('fics.db')
    cursor = conn.cursor()
    cursor.execute("SELECT title, author, url, fandoms, summary FROM fics")
    fics = cursor.fetchall()
    conn.close()

    cards_html = ""
    for fic in fics:
        title, author, url, fandoms, summary = fic
        cards_html += f'''
        <div class="bg-white p-6 rounded-lg shadow-md mb-4 border border-gray-200">
            <h2 class="text-xl font-bold text-indigo-600 mb-1">{title}</h2>
            <p class="text-sm text-gray-600 mb-2">Автор: <span class="font-semibold">{author}</span> | Фендом: <span class="font-semibold">{fandoms}</span></p>
            <p class="text-gray-700 text-sm mb-4">{summary}</p>
            <a href="{url}" target="_blank" class="inline-block bg-indigo-600 text-white px-4 py-2 rounded text-sm font-medium hover:bg-indigo-700">Читати на AO3 →</a>
        </div>
        '''

    return f'''
    <!DOCTYPE html>
    <html lang="uk">
    <head>
        <meta charset="UTF-8">
        <title>Вітрина Українських Фанфіків</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100 min-h-screen p-8">
        <div class="max-w-4xl mx-auto">
            <div class="flex justify-between items-center mb-8">
                <div>
                    <h1 class="text-3xl font-bold text-gray-900">Каталог Фанфіків (AO3)</h1>
                    <p class="text-sm text-gray-500">Записів у базі: {len(fics)}</p>
                </div>
                <a href="/update" class="bg-green-600 text-white px-4 py-2 rounded text-sm font-medium hover:bg-green-700">Оновити дані (100 робіт)</a>
            </div>
            {cards_html if cards_html else '<p class="text-gray-500">База порожня. Натисніть "Оновити дані (100 робіт)".</p>'}
        </div>
    </body>
    </html>
    '''

@app.get("/update")
def update_data(background_tasks: BackgroundTasks):
    background_tasks.add_task(fetch_ao3_ukrainian_100)
    return HTMLResponse('''
        <html>
            <body style="font-family: sans-serif; text-align: center; padding-top: 50px;">
                <h1>Запущено збір 100 фанфіків!</h1>
                <p>Процес іде у фоні (~15 секунд). Можеш повертатися на головну й оновлювати сторінку.</p>
                <a href="/" style="color: blue; font-weight: bold;">← Повернутися на головну</a>
            </body>
        </html>
    ''')
