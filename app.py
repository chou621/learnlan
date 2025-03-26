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
    return render_template("add.html")


# 修改問題頁面
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    if request.method == "POST":
        language = request.form["language"]
        question = request.form["question"]
        answer = request.form["answer"]
        timestamp = datetime.now()

        cur.execute(
            "UPDATE quiz_table SET language=%s, question=%s, answer=%s, timestamp=%s WHERE id=%s",
            (language, question, answer, timestamp, id),
        )
        conn.commit()
        return redirect(url_for("index"))

    cur.execute("SELECT * FROM quiz_table WHERE id=%s", (id,))
    question = cur.fetchone()
    return render_template("edit.html", question=question)


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
