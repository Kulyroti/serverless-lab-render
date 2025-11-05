from flask import Flask, request, jsonify
import psycopg2
import os
from urllib.parse import urlparse

app = Flask(__name__)

# Подключение к БД
DATABASE_URL = os.environ.get('DATABASE_URL')
conn = None

try:
    if DATABASE_URL:
        url = urlparse(DATABASE_URL)
        conn = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )

        # Создание таблицы при старте
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            conn.commit()
        print("✅ База данных подключена успешно")
    else:
        print("❌ DATABASE_URL не установлен")
except Exception as e:
    print(f"❌ Ошибка подключения к БД: {e}")


@app.route('/save', methods=['POST'])
def save_message():
    if not conn:
        return jsonify({"error": "DB not connected"}), 500

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data"}), 400

        message = data.get('message', '')

        with conn.cursor() as cur:
            cur.execute("INSERT INTO messages (content) VALUES (%s)", (message,))
            conn.commit()

        return jsonify({"status": "saved", "message": message})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/messages', methods=['GET'])
def get_messages():
    if not conn:
        return jsonify({"error": "DB not connected"}), 500

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, content, created_at FROM messages ORDER BY id DESC LIMIT 10")
            rows = cur.fetchall()

        messages = [{"id": r[0], "text": r[1], "time": r[2].isoformat()} for r in rows]
        return jsonify(messages)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "db_connected": conn is not None})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)