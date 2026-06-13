from flask import Flask, render_template, request, redirect
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)

DATA_FILE = "data.json"

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


# ----------------------
# データ
# ----------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return []


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ----------------------
# メイン画面
# ----------------------
@app.route("/")
def index():
    reservations = load_data()

    now = datetime.now()
    today = now.date()
    today_str = now.strftime("%Y-%m-%d")
    end_date = today + timedelta(days=7)
    current_time = now.strftime("%H:%M")

    # 未来だけ抽出（過去は消す）
    weekly = []
    for r in reservations:
        r_date = datetime.strptime(r["date"], "%Y-%m-%d").date()
        if r_date >= today:
            weekly.append(r)

    # 日付ごとにまとめる
    grouped = {}
    for r in weekly:
        grouped.setdefault(r["date"], []).append(r)

    grouped = dict(sorted(grouped.items()))

    # 予約済みスロット
    reserved_slots = {}
    for r in reservations:
        reserved_slots.setdefault(r["date"], []).append(r["slot"])

    # 使用中判定（今日だけ）
    in_use = False
    current_user = None

    for r in reservations:
        if r["date"] != today_str:
            continue

        start, end = r["slot"].split("-")

        if start <= current_time <= end:
            in_use = True
            current_user = r["name"]
            break

    return render_template(
        "index.html",
        grouped=grouped,
        today=today_str,
        in_use=in_use,
        current_user=current_user,
        slots=SLOTS,
        reserved_slots=reserved_slots
    )


# ----------------------
# 予約追加
# ----------------------
@app.route("/add", methods=["POST"])
def add():
    name = request.form["name"]
    date = request.form["date"]
    slot = request.form["slot"]

    # 過去禁止
    if datetime.strptime(date, "%Y-%m-%d").date() < datetime.now().date():
        return "過去は予約できません <a href='/'>戻る</a>"

    reservations = load_data()

    # 重複チェック
    for r in reservations:
        if r["date"] == date and r["slot"] == slot:
            return "その時間は予約済み <a href='/'>戻る</a>"

    reservations.append({
        "name": name,
        "date": date,
        "slot": slot
    })

    save_data(reservations)
    return redirect("/")


# ----------------------
# 削除
# ----------------------
@app.route("/delete", methods=["POST"])
def delete():
    reservations = load_data()

    target_date = request.form["date"]
    target_slot = request.form["slot"]
    target_name = request.form["name"]

    new_list = [
        r for r in reservations
        if not (
            r["date"] == target_date and
            r["slot"] == target_slot and
            r["name"] == target_name
        )
    ]

    save_data(new_list)
    return redirect("/")


# ----------------------
# 起動
# ----------------------
if __name__ == "__main__":
    app.run(debug=True)