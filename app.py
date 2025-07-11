import threading
import json
from flask import Flask, request
import requests
import config
import re

app = Flask(__name__)

# Константы из config.py
TOKEN = config.TOKEN
CONFIRMATION_TOKEN = config.CONFIRMATION_TOKEN
SECRET_KEY = config.SECRET_KEY
API_VERSION = config.API_VERSION

# Загрузка QA базы
with open("qa_data.json", encoding="utf-8") as f:
    qa_data = json.load(f)

# Загрузка словаря с нецензурной лексикой
with open("badwords.txt", encoding="utf-8") as f:
    bad_words = set(line.strip().lower() for line in f if line.strip())

# Проверка на мат
def contains_bad_words(text):
    words = re.findall(r'\w+', text.lower())
    return any(bw in words for bw in bad_words)

# Команда помощи
def show_help():
    return (
        "👋 Я бот VK Education!\n\n"
        "Я могу помочь с:\n"
        "• Поиском информации о проектах VK\n"
        "• Где и как смотреть вебинары\n"
        "• Ответами на частые вопросы\n\n"
        "Например, спроси:\n"
        "• Как выбрать проект?\n"
        "• Где найти вебинары?\n"
        "• Можно ли участвовать в нескольких проектах?\n\n"
        "Отправь /помощь в любой момент."
    )

# Поиск ответа по ключевым словам
def get_answer(message):
    msg = message.lower()

    if msg.startswith("/") or msg in ["помощь", "start", "начать"]:
        return show_help()

    for item in qa_data:
        if any(word in msg for word in item["keywords"]):
            return item["answer"]

    if msg.endswith("?") and any(x in msg for x in ["можно", "возможно", "разрешено", "доступно", "могу"]):
        return "Да."

    return None

# Отправка сообщения
def send_message(user_id, message):
    params = {
        "user_id": user_id,
        "message": message,
        "random_id": 0,
        "access_token": TOKEN,
        "v": API_VERSION
    }
    try:
        requests.post("https://api.vk.com/method/messages.send", params=params, timeout=2)
    except Exception as e:
        print("Ошибка отправки сообщения:", e)

# Обработка входящего сообщения
def process_message(data):
    message = data["object"]["message"]["text"]
    user_id = data["object"]["message"]["from_id"]

    if contains_bad_words(message):
        send_message(user_id, "⚠️ Пожалуйста, соблюдайте корректный стиль общения.")
    else:
        answer = get_answer(message)
        if answer:
            send_message(user_id, answer)
        else:
            send_message(user_id, "Извините, я пока не знаю ответа 😕\nПопробуйте найти информацию на сайте: https://edu.vk.com/projects")

# Обработка Callback от VK
@app.route("/", methods=["POST"])
def main():
    data = request.get_json()
    print("Получено событие:", data)

    if data.get("type") == "confirmation":
        return CONFIRMATION_TOKEN, 200

    if data.get("secret") != SECRET_KEY:
        return "invalid secret", 403

    if data.get("type") == "message_new":
        threading.Thread(target=process_message, args=(data,)).start()
        return "ok", 200

    return "ok", 200

# Запуск Flask-сервера
if __name__ == "__main__":
    from config import TOKEN, CONFIRMATION_TOKEN, SECRET_KEY
    app.run(host="0.0.0.0", port=5000)
