import json
import os
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(os.environ.get("PORT", 10000))

VK_TOKEN = os.environ.get("VK_TOKEN")
VK_CONFIRMATION = os.environ.get("VK_CONFIRMATION")
VK_SECRET = os.environ.get("VK_SECRET", "")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")

VK_API_VERSION = "5.199"


def send_vk_message(user_id: int, text: str):
    data = {
        "access_token": VK_TOKEN,
        "v": VK_API_VERSION,
        "user_id": user_id,
        "random_id": int(time.time() * 1000),
        "message": text,
    }

    body = urllib.parse.urlencode(data).encode("utf-8")

    req = urllib.request.Request(
        "https://api.vk.com/method/messages.send",
        data=body,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            print(response.read().decode("utf-8"))
    except Exception as e:
        print("VK send error:", e)


def get_biggest_photo_url(message: dict):
    attachments = message.get("attachments", [])

    for attachment in attachments:
        if attachment.get("type") != "photo":
            continue

        photo = attachment.get("photo", {})
        sizes = photo.get("sizes", [])

        if not sizes:
            continue

        biggest = max(
            sizes,
            key=lambda s: s.get("width", 0) * s.get("height", 0)
        )

        return biggest.get("url")

    return None


def analyze_food_photo(photo_url: str):
    if not OPENAI_API_KEY:
        return "Ошибка: OPENAI_API_KEY не задан в Render."

    payload = {
        "model": OPENAI_MODEL,
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "Ты нутрициолог. По фото блюда оцени калории. "
                            "Дай ответ на русском. Если точный вес неизвестен, "
                            "напиши примерную оценку и диапазон. Формат:\n\n"
                            "🍽 Блюдо: ...\n"
                            "⚖️ Примерный вес: ...\n"
                            "🔥 Калории: ... ккал\n"
                            "🥩 БЖУ: белки ... г, жиры ... г, углеводы ... г\n"
                            "💬 Комментарий: ..."
                        )
                    },
                    {
                        "type": "input_image",
                        "image_url": photo_url
                    }
                ]
            }
        ]
    }

    body = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))

        return result.get("output_text", "Не удалось получить ответ от ИИ.")

    except Exception as e:
        print("OpenAI error:", e)
        return "Ошибка при анализе фото. Попробуй ещё раз позже."


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"VK calorie bot is alive")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length)

        try:
            data = json.loads(raw_body.decode("utf-8"))
        except Exception as e:
            print("JSON error:", e)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
            return

        print("VK event:", data)

        if VK_SECRET:
            if data.get("secret") != VK_SECRET:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"ok")
                return

        event_type = data.get("type")

        if event_type == "confirmation":
            self.send_response(200)
            self.end_headers()
            self.wfile.write((VK_CONFIRMATION or "").encode("utf-8"))
            return

        if event_type == "message_new":
            message = data.get("object", {}).get("message", {})
            user_id = message.get("from_id")
            text = (message.get("text") or "").strip()

            if user_id:
                photo_url = get_biggest_photo_url(message)

                if text == "/start":
                    send_vk_message(
                        user_id,
                        "Привет 👋\n\n"
                        "Я считаю калории по фото еды.\n"
                        "Просто отправь мне фото блюда."
                    )

                elif text == "/help":
                    send_vk_message(
                        user_id,
                        "Команды:\n"
                        "/start — запуск\n"
                        "/help — помощь\n\n"
                        "Чтобы посчитать калории, отправь фото еды."
                    )

                elif photo_url:
                    send_vk_message(user_id, "Фото получил 📸 Считаю калории...")
                    result = analyze_food_photo(photo_url)
                    send_vk_message(user_id, result)

                else:
                    send_vk_message(
                        user_id,
                        "Отправь фото блюда, и я примерно посчитаю калории 🍽"
                    )

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")


server = HTTPServer(("0.0.0.0", PORT), Handler)
print(f"Server started on port {PORT}")
server.serve_forever()
