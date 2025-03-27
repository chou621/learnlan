import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
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


@app.route("/delete/<question>", methods=["DELETE"])
def delete_question(question):
    cur.execute("DELETE FROM quiz_table WHERE question=%s", (question,))
    conn.commit()
    return jsonify({"success": True})


# 檢查問題是否重複
@app.route("/check_duplicate/<question>")
def check_duplicate(question):
    cur.execute("SELECT COUNT(*) FROM quiz_table WHERE question = %s", (question,))
    count = cur.fetchone()[0]
    return jsonify({"exists": count > 0})


# 刪除多個問題
@app.route("/delete_multiple", methods=["POST"])
def delete_multiple():
    data = request.get_json()
    questions = data.get("questions", [])
    try:
        cur.executemany(
            "DELETE FROM quiz_table WHERE question = %s", [(q,) for q in questions]
        )
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        print("Delete multiple error:", e)
        return jsonify({"success": False, "error": str(e)})


@app.route("/update/<original_question>", methods=["PUT"])
def update_question(original_question):
    data = request.get_json()
    language = data.get("language")
    question = data.get("question")
    answer = data.get("answer")
    timestamp = datetime.now()

    cur.execute(
        "UPDATE quiz_table SET language=%s, question=%s, answer=%s, timestamp=%s WHERE question=%s",
        (language, question, answer, timestamp, original_question),
    )
    conn.commit()
    return jsonify({"success": True})


@app.route("/add")
def add_page():
    return render_template("add_quiz.html")


from flask import send_from_directory  # 確保這行有 import


@app.route("/play_audio/<question>")
def play_audio(question):
    cur.execute("SELECT language FROM quiz_table WHERE question = %s", (question,))
    result = cur.fetchone()

    if not result:
        return jsonify({"success": False, "message": "Question not found"}), 404

    language = result[0]
    sanitized_question = question.replace("/", "_")  # 防止路徑錯誤
    filename = f"{sanitized_question}.mp3"
    filepath = os.path.join("audio", filename)

    # 如果音檔已經存在，直接送出
    if os.path.exists(filepath):
        return send_from_directory("audio", filename)

    # 否則生成音檔
    try:
        tts = gTTS(text=question, lang=language)
        tts.save(filepath)
        return send_from_directory("audio", filename)
    except Exception as e:
        print("🔴 TTS 失敗:", e)
        return jsonify({"success": False, "message": "語音產生失敗"}), 500


@app.route("/get_quiz_data")
def get_quiz_data():
    num = int(request.args.get("numOfQuestions", 10))
    cur.execute("SELECT * FROM quiz_table ORDER BY RANDOM() LIMIT %s", (num,))
    data = cur.fetchall()
    quizzes = [
        {"language": row[1], "question": row[2], "answer": row[3]} for row in data
    ]
    return jsonify({"questions": quizzes})


@app.route("/get_reverse_quiz_data")
def get_reverse_quiz_data():
    num = int(request.args.get("numOfQuestions", 10))
    cur.execute("SELECT * FROM quiz_table ORDER BY RANDOM() LIMIT %s", (num,))
    quizzes = cur.fetchall()
    return jsonify(
        {
            "questions": [
                {"question": row[2], "answer": row[3], "language": row[1]}
                for row in quizzes
            ]
        }
    )


@app.route("/quiz")
def quiz():
    num = int(request.args.get("numOfQuestions", 10))
    cur.execute(
        "SELECT language, question, answer FROM quiz_table ORDER BY RANDOM() LIMIT %s",
        (num,),
    )
    quiz_rows = cur.fetchall()

    quizData = [{"language": q[0], "question": q[1], "answer": q[2]} for q in quiz_rows]
    cur.execute("SELECT language, question, answer FROM quiz_table")
    all_quiz_rows = cur.fetchall()
    ALL_quizData = [
        {"language": q[0], "question": q[1], "answer": q[2]} for q in all_quiz_rows
    ]

    return render_template("quiz.html", quizData=quizData, ALL_quizData=ALL_quizData)


@app.route("/reverse_quiz")
def reverse_quiz():
    return render_template("reverse_quiz.html")


def preload_all_audio():
    cur.execute("SELECT question, language FROM quiz_table")
    for question, lang in cur.fetchall():
        filename = f"{question.replace('/', '_')}.mp3"
        filepath = os.path.join("audio", filename)
        if not os.path.exists(filepath):
            try:
                tts = gTTS(text=question, lang=lang)
                tts.save(filepath)
            except Exception as e:
                print(f"🔴 無法為 {question} 產生語音: {e}")


preload_all_audio()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
