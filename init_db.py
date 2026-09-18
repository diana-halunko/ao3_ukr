import sqlite3

conn = sqlite3.connect('ao3_catalog.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS works (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ao3_id TEXT UNIQUE,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    fandom TEXT,
    url TEXT NOT NULL
)
''')

# Додаємо тестові дані
cursor.execute('''
INSERT OR IGNORE INTO works (ao3_id, title, author, fandom, url)
VALUES 
('1', 'Тестовий фанфік №1', 'Автор_1', 'Гаррі Поттер', 'https://archiveofourown.org'),
('2', 'Тестовий фанфік №2', 'Автор_2', 'Відьмак', 'https://archiveofourown.org')
''')

conn.commit()
conn.close()
print("Базу даних 'ao3_catalog.db' створено та заповнено тестовими даними!")
