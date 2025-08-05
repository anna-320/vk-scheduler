import requests
import schedule
import time
import json
import os
from datetime import datetime

# === Настройки ===
TOKEN = os.getenv("VK_TOKEN", "твой_токен_здесь")
CHAT_ID = int(os.getenv("CHAT_ID", 123))
PEER_ID = 2000000000 + CHAT_ID
API_VERSION = "5.199"
MESSAGES_FILE = "messages.json"

def get_upload_server():
    url = "https://api.vk.com/method/photos.getMessagesUploadServer"
    params = {"peer_id": PEER_ID, "v": API_VERSION, "access_token": TOKEN}
    response = requests.get(url, params=params).json()
    return response["response"]["upload_url"]

def save_photo_on_server(upload_url, file_path):
    files = {"photo": open(file_path, "rb")}
    response = requests.post(upload_url, files=files).json()
    save_url = "https://api.vk.com/method/photos.saveMessagesPhoto"
    params = {
        "v": API_VERSION,
        "access_token": TOKEN,
        "photo": response["photo"],
        "server": response["server"],
        "hash": response["hash"]
    }
    result = requests.post(save_url, params=params).json()
    photo = result["response"][0]
    return f"photo{photo['owner_id']}_{photo['id']}"

def send_vk_message(message, attachment=None):
    url = "https://api.vk.com/method/messages.send"
    params = {
        "peer_id": PEER_ID,
        "message": message,
        "random_id": int(time.time() * 1000000),
        "v": API_VERSION
    }
    if attachment:
        params["attachment"] = attachment

    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.post(url, params=params, headers=headers)
    data = response.json()

    if "response" in data:
        print(f"✅ Отправлено: {message}")
        return True
    else:
        error_msg = data.get("error", {}).get("error_msg", "Неизвестная ошибка")
        print(f"❌ Ошибка отправки: {error_msg}")
        return False

def load_messages():
    try:
        with open(MESSAGES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Не удалось прочитать messages.json: {e}")
        return []

def save_messages(messages):
    try:
        with open(MESSAGES_FILE, "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Не удалось сохранить messages.json: {e}")

def check_and_send():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    messages = load_messages()
    sent = []

    for msg in messages:
        scheduled = f"{msg['date']} {msg['time']}"
        if scheduled == now:
            attachment = None
            if msg.get("photo") and os.path.exists(msg["photo"]):
                try:
                    upload_url = get_upload_server()
                    attachment = save_photo_on_server(upload_url, msg["photo"])
                except Exception as e:
                    print(f"⚠️ Ошибка загрузки фото {msg['photo']}: {e}")

            if send_vk_message(msg["message"], attachment):
                sent.append(msg)

    # Удаляем отправленные
    remaining = [m for m in messages if m not in sent]
    save_messages(remaining)
    print(f"📩 Осталось в очереди: {len(remaining)}")

# Проверяем каждую минуту
schedule.every().minute.at(":00").do(check_and_send)

print("🤖 Бот запущен и проверяет сообщения каждую минуту...")
while True:
    schedule.run_pending()
    time.sleep(1)
