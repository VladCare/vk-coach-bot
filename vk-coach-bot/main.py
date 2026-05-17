import base64
import json
import os
import time
import threading
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


PORT = int(os.environ.get("PORT", 10000))

VK_TOKEN = (os.environ.get("VK_TOKEN") or "").strip()
VK_CONFIRMATION = (os.environ.get("VK_CONFIRMATION") or "").strip()
VK_SECRET = (os.environ.get("VK_SECRET") or "").strip()

OPENAI_API_KEY = (os.environ.get("OPENAI_API_KEY") or "").strip()
OPENAI_MODEL = (os.environ.get("OPENAI_MODEL") or "gpt-4o-mini").strip()

VK_API_VERSION = "5.199"


def send_vk_message(user_id: int, text: str):
    if not VK_TOKEN:
        print("VK_TOKEN is missing")
        return

    if not text:
        text = "Пустой ответ."

    # VK не любит слишком длинные сообщения
    chunks = [text[i:i + 3500] for i in range(0, len(text), 3500)]

    for chunk in chunks:
        data = {
            "access_token": VK_TOKEN,
            "v": VK_API_VERSION,
            "user_id": user_id,
            "random_id": int(time.time() * 1000000),
            "message": chunk,
        }

        body = urllib.parse.urlencode(data).encode("utf-8")

        req = urllib.request.Request(
            "https://api.vk.com/method/messages.send",
            data=body,
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                print("VK send:", response.read().decode("utf-8"))
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


def download_image_as_data_url(photo_url: str):
    req = urllib.request.Request(
        photo_url,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
        method="GET",
    )

    with urllib.request.urlopen(req, timeout=30) as response:
        image_bytes = response.read()
        content_type = response.headers.get("Content-Type", "image/jpeg")

    if not content_type.startswith("image/"):
        content_type = "image/jpeg"

    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{content_type};base64,{image_base64}"


def extract_openai_error(error_text: str):
    try:
        data = json.loads(error_text)
        error = data.get("error", {})
        message = error.get("message")
        if message:
            return message
    except Exception:
        pass

    return error_text[:500]


def analyze_food_photo(photo_url: str):
    if not OPENAI_API_KEY:
        return "Ошибка: OPENAI_API_KEY не задан в Render."

    try:
        image_data_url = download_image_as_data_url(photo_url)
    except Exception as e:
        print("Image download error:", e)
        return "Не смог скачать фото из VK. Попробуй отправить фото ещё раз."

    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Ты помощник-нутрициолог. Твоя задача — примерно оценивать "
                    "калории и БЖУ по фото еды. Не выдумывай точный вес, если его "
                    "нельзя определить. Всегда указывай, что это приблизительная оценка."
                )
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Оцени блюдо на фото. Ответь строго на русском языке.\n\n"
                            "Формат ответа:\n"
                            "🍽 Блюдо: ...\n"
                            "⚖️ Примерный вес: ...\n"
                            "🔥 Калории: ... ккал\n"
                            "🥩 БЖУ: белки ... г, жиры ... г, углеводы ... г\n"
                            "💬 Комментарий: ...\n\n"
                            "Если на фото несколько продуктов, перечисли их отдельно."
                        )
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_data_url
                        }
                    }
                ]
            }
        ],
        "max_tokens": 700,
        "temperature": 0.2,
    }

    body = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            raw = response.read().decode("utf-8")
            result = json.loads(raw)

        answer = (
            result
            .get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )

        if answer:
            return answer

        print("OpenAI raw result:", result)
        return "ИИ ответил, но текст ответа не найден. Проверь Render Logs."

    except urllib.error.HTTPError as e:
        error_text = e.read().decode("utf-8", errors="ignore")
        print("OpenAI HTTP error:", error_text)

        short_error = extract_openai_error(error_text)

        return (
            "Ошибка OpenAI API.\n\n"
            f"Причина: {short_error}\n\n"
            "Проверь OPENAI_API_KEY, баланс аккаунта и модель OPENAI_MODEL."
        )

    except Exception as e:
        print("OpenAI error:", e)
        return "Ошибка при анализе фото. Попробуй ещё раз позже."


def process_food_photo(user_id: int, photo_url: str):
    send_vk_message(user_id, "Фото получил 📸 Считаю калории...")

    result = analyze_food_photo(photo_url)

    send_vk_message(user_id, result)


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

        event_type = data.get("type")

        if event_type == "confirmation":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(VK_CONFIRMATION.encode("utf-8"))
            return

        if VK_SECRET:
            if data.get("secret") != VK_SECRET:
                print("Wrong VK secret")
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"ok")
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
                        "Просто отправь мне фото блюда 🍽"
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
                    thread = threading.Thread(
                        target=process_food_photo,
                        args=(user_id, photo_url),
                        daemon=True,
                    )
                    thread.start()

                else:
                    send_vk_message(
                        user_id,
                        "Отправь фото блюда, и я примерно посчитаю калории 🍽"
                    )

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Server started on port {PORT}")
    server.serve_forever()
