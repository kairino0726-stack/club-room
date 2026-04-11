from flask import Flask, render_template, request, redirect
import json
import os
from datetime import datetime

app = Flask(__name__)

DATA_FILE = "data.json"

# 固定の時間枠
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


def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@app.route("/")
def index():
    reservations = load_data()

    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")

    # カレンダー作成
    calendar = {}

    for r in reservations:
        date = r["date"]
        if date not in calendar:
            calendar[date] = []
        calendar[date].append(r)

    # 使用中判定
    in_use = False
    current_user = None

    for r in reservations:
        if r["date"] != today:
            continue

        start, end = r["slot"].split("-")

        if start <= current_time <= end:
            in_use = True
            current_user = r["name"]
            break

    return render_template(
        "index.html",
        reservations=reservations,
        calendar=calendar,
        today=today,
        in_use=in_use,
        current_user=current_user,
        slots=SLOTS
    )


@app.route("/add", methods=["POST"])
def add():
    name = request.form["name"]
    date = request.form["date"]
    slot = request.form["slot"]

    reservations = load_data()

    # 重複チェック
    for r in reservations:
        if r["date"] == date and r["slot"] == slot:
            return "この時間は予約済み！<br><a href='/'>戻る</a>"

    reservations.append({
        "name": name,
        "date": date,
        "slot": slot
    })

    save_data(reservations)
    return redirect("/")


@app.route("/delete/<int:index>")
def delete(index):
    reservations = load_data()

    if 0 <= index < len(reservations):
        reservations.pop(index)

    save_data(reservations)
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)