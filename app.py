from flask import Flask, request, Response
import json
import requests
from config import TOKEN, CONFIRMATION_TOKEN, SECRET_KEY, API_VERSION

app = Flask(__name__)

# Загружаем QA-данные
with open("qa_data.json", "r", encoding="utf-8") as f:
    qa_data = json.load(f)

# Загружаем список нецензурных слов
with open("badwords.txt", "r", encoding="utf-8") as f:
    bad_words = set(line.strip().lower() for line in f if line.strip())

# Проверка на мат
def contains_bad_words(text):
    return any(word in text.lower() for word in bad_words)

# Ответ на вопрос
def get_answer(message):
    msg = message.lower()
    for question in qa_data:
        if question in msg:
            return qa_data[question]
    if msg.endswith("?") and any(x in msg for x in ["можно", "возможно", "разрешено", "доступно", "могу"]):
        return "Да."
    return None

# Отправка ответа в VK
def send_message(user_id, message):
    params = {
        "user_id": user_id,
        "message": message,
        "random_id": 0,
        "access_token": TOKEN,
        "v": API_VERSION
    }
    requests.post("https://api.vk.com/method/messages.send", params=params)

# Главная точка входа
@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()

    # VK проверяет подтверждение сервера
    if data.get("type") == "confirmation":
        return Response(CONFIRMATION_TOKEN, status=200, mimetype='text/plain')

    # Проверка секрета
    if data.get("secret") != SECRET_KEY:
        return Response("invalid secret", status=403)

    # Новое сообщение от пользователя
    if data.get("type") == "message_new":
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
                    "Извините, я пока не знаю ответа 😕\nПопробуйте найти информацию на сайте: https://edu.vk.com/projects")

    return Response("ok", status=200)

# Запуск (важно для Railway)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
