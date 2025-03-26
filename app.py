import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, jsonify
from gtts import gTTS
from datetime import datetime

app = Flask(__name__)

# 連接 PostgreSQL
DATABASE_URL = "postgresql://learnlan_user:bLkEFJiTiF4FgWGCRWwvKikKkQfUyjJZ@dpg-cvhunsggph6c73cg2oig-a/learnlan"
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# 初始化資料庫，如果沒有資料表就建立
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


# 主頁：顯示所有問題
@app.route("/")
def index():
    cur.execute("SELECT * FROM quiz_table")
    questions = cur.fetchall()
    return render_template("index.html", questions=questions)


# 新增問題頁面
@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        language = request.form["language"]
        question = request.form["question"]
        answer = request.form["answer"]
        timestamp = datetime.now()

        cur.execute(
            "INSERT INTO quiz_table (language, question, answer, timestamp) VALUES (%s, %s, %s, %s)",
            (language, question, answer, timestamp),
        )
        conn.commit()
        return redirect(url_for("index"))
    return render_template("add_quiz.html")


@app.route("/check_duplicate/<question>")
def check_duplicate(question):
    try:
        cur.execute("SELECT * FROM quiz_table WHERE question = %s", (question,))
        existing = cur.fetchone()
        if existing:
            return jsonify({"exists": True})
        else:
            return jsonify({"exists": False})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/update/<path:old_question>", methods=["PUT"])
def update_quiz_by_question(old_question):
    data = request.get_json()
    new_question = data.get("question")
    answer = data.get("answer")
    language = data.get("language")
    timestamp = datetime.now()

    cur.execute(
        "UPDATE quiz_table SET language=%s, question=%s, answer=%s, timestamp=%s WHERE question=%s",
        (language, new_question, answer, timestamp, old_question),
    )
    conn.commit()
    return jsonify({"success": True})


# 刪除問題
@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    cur.execute("DELETE FROM quiz_table WHERE id=%s", (id,))
    conn.commit()
    return redirect(url_for("index"))


# 讀取語音
@app.route("/speech/<int:id>")
def speech(id):
    cur.execute("SELECT question FROM quiz_table WHERE id=%s", (id,))
    question = cur.fetchone()
    tts = gTTS(question[0], lang="ko")
    tts.save("static/question.mp3")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
