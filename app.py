from flask import Flask, send_from_directory, request, jsonify
import os

app = Flask(__name__, static_folder='public')

# In-memory list for reviews (will reset when serverless function sleeps)
REVIEWS = []

@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    return jsonify(REVIEWS)

@app.route('/api/reviews', methods=['POST'])
def post_review():
    data = request.json
    name = data.get('name', 'Anonymous')
    handle = data.get('handle', '@user')
    rating = data.get('rating', '★★★★★')
    content = data.get('content', '')
    if content.strip():
        # Add to the beginning of the list so newest are first
        REVIEWS.insert(0, {"name": name, "handle": handle, "rating": rating, "content": content})
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
