from flask import Flask, request
import json
import requests
from config import TOKEN, CONFIRMATION_TOKEN, SECRET_KEY, API_VERSION

app = Flask(__name__)

# Загружаем базу данных
with open("qa_data.json", "r", encoding="utf-8") as f:
    qa_data = json.load(f)

# Загружаем список нецензурных слов
with open("badwords.txt", "r", encoding="utf-8") as f:
    bad_words = set(line.strip().lower() for line in f if line.strip())

# Фильтр мата
def contains_bad_words(text):
    return any(bad_word in text.lower() for bad_word in bad_words)

# Поиск ответа
def get_answer(message):
    msg = message.lower()
    for question in qa_data:
        if question in msg:
            return qa_data[question]

    # Ответ на закрытые "да/нет" вопросы
    if msg.endswith("?") and any(word in msg for word in ["возможно", "можно", "могу", "доступно", "разрешено"]):
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
    requests.post("https://api.vk.com/method/messages.send", params=params)

# Обработка запросов от VK
@app.route("/", methods=["POST"])
def vk_webhook():
    data = request.json

    # Подтверждение адреса сервера
    if data["type"] == "confirmation":
        return CONFIRMATION_TOKEN

    # Проверка подлинности запроса
    if "secret" in data and data["secret"] != SECRET_KEY:
        return "invalid secret"

    # Обработка новых сообщений
    if data["type"] == "message_new":
        user_id = data["object"]["message"]["from_id"]
        message = data["object"]["message"]["text"]

        if contains_bad_words(message):
            send_message(user_id, "Пожалуйста, соблюдайте корректный стиль общения.")
        else:
            response = get_answer(message)
            if response:
                send_message(user_id, response)
            else:
                send_message(user_id,
                    "Извините, я пока не знаю ответа 😕\nПопробуйте найти информацию на сайте: https://edu.vk.com/projects или напишите в поддержку.")

    return "ok"

# Запуск приложения
if __name__ == "__main__":
    app.run(port=5000)
