import os
import threading
import json
import re
from difflib import get_close_matches
from flask import Flask, request
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

TOKEN = os.environ.get("TOKEN")
CONFIRMATION_TOKEN = os.environ.get("CONFIRMATION_TOKEN")
SECRET_KEY = os.environ.get("SECRET_KEY")
API_VERSION = "5.199"

with open("qa_data.json", encoding="utf-8") as f:
    qa_data = json.load(f)

with open("badwords.txt", encoding="utf-8") as f:
    bad_words = set(line.strip().lower() for line in f if line.strip())

def contains_bad_words(text):
    words = re.findall(r'\w+', text.lower())
    return any(word in bad_words for word in words)

def get_answer(message):
    msg = message.lower()

    # Точное совпадение
    if msg in qa_data:
        return qa_data[msg]

    # Похожие вопросы
    matches = get_close_matches(msg, qa_data.keys(), n=1, cutoff=0.6)
    if matches:
        return qa_data[matches[0]]

    # Проверка на закрытые вопросы
    if msg.endswith("?") and any(x in msg for x in ["можно", "возможно", "разрешено", "доступно", "могу"]):
        return "Да."

    return None

def search_elsewhere_response():
    return ("Этот вопрос не относится к проектам VK Education. "
            "Попробуйте воспользоваться поиском в интернете или уточните запрос.")

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
            send_message(user_id,
                         "Извините, я пока не знаю ответа 😕\n"
                         "Попробуйте найти информацию на сайте: https://edu.vk.com/projects\n\n" +
                         search_elsewhere_response())

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
