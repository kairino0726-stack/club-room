from flask import Flask, render_template, request, redirect
import psycopg2
import os
from datetime import datetime

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")

WEEKDAYS = ["月", "火", "水", "木", "金", "土", "日"]

SLOTS = [
    "09:00-10:30",
    "10:40-12:10",
    "12:10-13:00",
    "13:00-14:30",
    "14:40-16:10",
    "16:20-17:50",
    "18:00-19:30",
    "19:30-21:00"
]


def get_connection():
    return psycopg2.connect(DATABASE_URL)


# テーブル作成
conn = get_connection()
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS reservations (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    date TEXT NOT NULL,
    slot TEXT NOT NULL
)
""")

conn.commit()
cur.close()
conn.close()


@app.route("/")
def index():

    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")

    selected_date = request.args.get("date", today_str)

    date_obj = datetime.strptime(selected_date, "%Y-%m-%d")
    selected_day = WEEKDAYS[date_obj.weekday()]

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT name, date, slot
    FROM reservations
    WHERE date=%s
    ORDER BY slot
    """, (selected_date,))

    rows = cur.fetchall()

    reservations = []

    for row in rows:
        reservations.append({
            "name": row[0],
            "date": row[1],
            "slot": row[2]
        })

    # 使用中判定
    in_use = False
    current_user = None

    now_time = now.time()

    cur.execute("""
    SELECT name, slot
    FROM reservations
    WHERE date=%s
    """, (today_str,))

    today_rows = cur.fetchall()

    for row in today_rows:

        start_str, end_str = row[1].split("-")

        start_time = datetime.strptime(start_str, "%H:%M").time()
        end_time = datetime.strptime(end_str, "%H:%M").time()

        if start_time <= now_time <= end_time:
            in_use = True
            current_user = row[0]
            break

    cur.close()
    conn.close()

    return render_template(
        "index.html",
        today=today_str,
        selected_date=selected_date,
        selected_day=selected_day,
        reservations=reservations,
        in_use=in_use,
        current_user=current_user,
        slots=SLOTS
    )


@app.route("/add", methods=["POST"])
def add():

    name = request.form["name"]
    date = request.form["date"]
    slot = request.form["slot"]

    if datetime.strptime(date, "%Y-%m-%d").date() < datetime.now().date():
        return "過去の日付は予約できません"

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT *
    FROM reservations
    WHERE date=%s AND slot=%s
    """, (date, slot))

    if cur.fetchone():
        cur.close()
        conn.close()
        return "その時間帯は予約済みです"

    cur.execute("""
    INSERT INTO reservations (name, date, slot)
    VALUES (%s, %s, %s)
    """, (name, date, slot))

    conn.commit()

    cur.close()
    conn.close()

    return redirect("/?date=" + date)


@app.route("/delete", methods=["POST"])
def delete():

    target_date = request.form["date"]
    target_slot = request.form["slot"]
    target_name = request.form["name"]

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    DELETE FROM reservations
    WHERE date=%s
    AND slot=%s
    AND name=%s
    """, (target_date, target_slot, target_name))

    conn.commit()

    cur.close()
    conn.close()

    return redirect("/?date=" + target_date)


if __name__ == "__main__":
    app.run(debug=True)
