import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, jsonify
from gtts import gTTS
from datetime import datetime

app = Flask(__name__)

DATABASE_URL = "postgresql://learnlan_user:bLkEFJiTiF4FgWGCRWwvKikKkQfUyjJZ@dpg-cvhunsggph6c73cg2oig-a/learnlan"
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute(
    """
CREATE TABLE IF NOT EXISTS quiz_table (
    id SERIAL PRIMARY KEY,
    language TEXT NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL
)
"""
)
conn.commit()


@app.route("/")
def index():
    cur.execute("SELECT * FROM quiz_table")
    rows = cur.fetchall()
    quizzes = [
        {
            "id": row[0],
            "language": row[1],
            "question": row[2],
            "answer": row[3],
            "timestamp": row[4],
        }
        for row in rows
    ]
    return render_template("index.html", quizzes=quizzes)


@app.route("/add", methods=["POST"])
def add():
    language = request.json.get("language")
    question = request.json.get("question")
    answer = request.json.get("answer")
    timestamp = datetime.now()
    try:
        cur.execute(
            "INSERT INTO quiz_table (language, question, answer, timestamp) VALUES (%s, %s, %s, %s)",
            (language, question, answer, timestamp),
        )
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        print("Add error:", e)
        return jsonify({"success": False, "error": str(e)})


@app.route("/add")
def add_page():
    return render_template("add_quiz.html")


@app.route("/play_audio/<question>")
def play_audio(question):
    from gtts import gTTS
    import tempfile

    # 先查出這個 question 的語言
    cur.execute("SELECT language FROM quiz_table WHERE question = %s", (question,))
    result = cur.fetchone()
    if not result:
        return "Question not found", 404

    language = result[0]

    # 產生語音
    tts = gTTS(question, lang=language)

    # 建立暫存檔
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp.name)
    temp.close()

    return send_file(temp.name, mimetype="audio/mpeg")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
