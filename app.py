from flask import Flask, request, Response
import json
import requests
import threading
from config import TOKEN, CONFIRMATION_TOKEN, SECRET_KEY, API_VERSION

app = Flask(__name__)

with open("qa_data.json", "r", encoding="utf-8") as f:
    qa_data = json.load(f)

with open("badwords.txt", "r", encoding="utf-8") as f:
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
    except requests.exceptions.RequestException:
        pass

def send_message_async(user_id, message):
    thread = threading.Thread(target=send_message, args=(user_id, message))
    thread.start()

@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()

    if data.get("type") == "confirmation":
        return Response(CONFIRMATION_TOKEN, status=200, mimetype='text/plain')

    if data.get("secret") != SECRET_KEY:
        return Response("invalid secret", status=403)

    if data.get("type") == "message_new":
        message = data["object"]["message"]["text"]
        user_id = data["object"]["message"]["from_id"]

        if contains_bad_words(message):
            send_message_async(user_id, "Пожалуйста, соблюдайте корректный стиль общения.")
        else:
            answer = get_answer(message)
            if answer:
                send_message_async(user_id, answer)
            else:
                send_message_async(user_id,
                    "Извините, я пока не знаю ответа 😕\nПопробуйте найти информацию на сайте: https://edu.vk.com/projects")

    # Важно: возвращаем ok сразу, не дожидаясь отправки сообщений
    return Response("ok", status=200)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)
