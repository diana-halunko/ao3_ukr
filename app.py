from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('ao3_catalog.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    conn = get_db_connection()
    works = conn.execute('SELECT * FROM works LIMIT ? OFFSET ?', (per_page, offset)).fetchall()
    total_works = conn.execute('SELECT COUNT(*) FROM works').fetchone()[0]
    conn.close()

    total_pages = (total_works + per_page - 1) // per_page

    return render_template('index.html', works=works, page=page, total_pages=total_pages)

if __name__ == '__main__':
    app.run(debug=True)
