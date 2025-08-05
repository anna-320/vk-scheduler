from flask import Flask, render_template, request, redirect, url_for
import json
import os
from datetime import datetime

app = Flask(__name__)
MESSAGES_FILE = "messages.json"

def load_messages():
    if not os.path.exists(MESSAGES_FILE):
        return []
    try:
        with open(MESSAGES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Не удалось прочитать {MESSAGES_FILE}: {e}")
        return []

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        message = request.form["message"].strip()
        date = request.form["date"]
        time = request.form["time"]

        photo = None
        if "photo" in request.files:
            file = request.files["photo"]
            if file and file.filename != "":
                filename = f"{int(datetime.now().timestamp())}_{file.filename}"
                filepath = os.path.join("uploads", filename)
                os.makedirs("uploads", exist_ok=True)
                file.save(filepath)
                photo = f"uploads/{filename}"

        new_msg = {
            "date": date,
            "time": time,
            "message": message,
            "photo": photo
        }

        messages = load_messages()
        messages.append(new_msg)
        save_messages(messages)
        return redirect(url_for("index"))

    messages = load_messages()
    return render_template("index.html", messages=messages)

def save_messages(messages):
    with open(MESSAGES_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
