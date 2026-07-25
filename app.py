from flask import Flask, send_from_directory, request, jsonify
import os
import sqlite3

app = Flask(__name__, static_folder='public')

# Initialize DB
def init_db():
    conn = sqlite3.connect('reviews.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reviews
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, handle TEXT, rating TEXT, content TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    conn = sqlite3.connect('reviews.db')
    c = conn.cursor()
    c.execute('SELECT name, handle, rating, content FROM reviews ORDER BY id DESC')
    reviews = [{"name": row[0], "handle": row[1], "rating": row[2], "content": row[3]} for row in c.fetchall()]
    conn.close()
    return jsonify(reviews)

@app.route('/api/reviews', methods=['POST'])
def post_review():
    data = request.json
    name = data.get('name', 'Anonymous')
    handle = data.get('handle', '@user')
    rating = data.get('rating', '★★★★★')
    content = data.get('content', '')
    if content.strip():
        conn = sqlite3.connect('reviews.db')
        c = conn.cursor()
        c.execute('INSERT INTO reviews (name, handle, rating, content) VALUES (?, ?, ?, ?)', (name, handle, rating, content))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"}), 201
    return jsonify({"status": "error", "message": "Content required"}), 400

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(app.static_folder, path)

if __name__ == '__main__':
    print("[Info] TinPyUI Showcase Server on http://localhost:5000")
    app.run(debug=True, port=5000)
