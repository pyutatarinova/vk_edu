import os
import threading
from flask import Flask, request

import requests
import json

app = Flask(__name__)

TOKEN = os.environ.get("TOKEN")  # Токен сообщества
CONFIRMATION_TOKEN = os.environ.get("CONFIRMATION_TOKEN")  # Строка подтверждения (например, "cb504bf8")
SECRET_KEY = os.environ.get("SECRET_KEY")  # Секретный ключ Callback API
API_VERSION = "5.199"

# Загружаем данные и мат-фильтр, как у тебя
with open("qa_data.json", encoding="utf-8") as f:
    qa_data = json.load(f)

with open("badwords.txt", encoding="utf-8") as f:
    bad_words = set(line.strip().lower() for line in f if line.strip())

def contains_bad_words(text):
    return any(word in text.lower() for word in bad_words)

def get_answer(message):
    msg = message.lower()
    for question in qa_data:
        if question in msg:
            return qa_data[question]
    if msg.endswith("?") and any(x in msg for x in ["можно", "возможно", "разрешено", "доступно", "могу"]):
        return "Да."
    return None

def send_message(user_id, message):
    params = {
        "user_id": user_id,
        "message": message,
        "random_id": 0,
        "access_token": TOKEN,
        "v": API_VERSION
    }
    try:
        requests.post("https://api.vk.com/method/messages.send", params=params, timeout=1)
    except Exception as e:
        print("Error sending message:", e)

def process_message(data):
    message = data["object"]["message"]["text"]
    user_id = data["object"]["message"]["from_id"]

    if contains_bad_words(message):
        send_message(user_id, "Пожалуйста, соблюдайте корректный стиль общения.")
    else:
        answer = get_answer(message)
        if answer:
            send_message(user_id, answer)
        else:
            send_message(user_id, "Извините, я пока не знаю ответа 😕\nПопробуйте найти информацию на сайте: https://edu.vk.com/projects")

@app.route("/", methods=["POST"])
def main():
    data = request.get_json()
    print("Received event:", data)

    if data.get("type") == "confirmation":
        return CONFIRMATION_TOKEN, 200

    if data.get("secret") != SECRET_KEY:
        return "invalid secret", 403

    if data.get("type") == "message_new":
        threading.Thread(target=process_message, args=(data,)).start()
        return "ok", 200

    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

