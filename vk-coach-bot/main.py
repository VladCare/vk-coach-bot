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

VK_API_VERSION = "5.199"


def send_vk_message(user_id: int, text: str):
    if not VK_TOKEN:
        print("VK_TOKEN is missing")
        return

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
        with urllib.request.urlopen(req, timeout=10) as response:
            print(response.read().decode("utf-8"))
    except Exception as e:
        print("VK send error:", e)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"VK callback bot is alive")

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
            text = message.get("text", "")

            if user_id:
                if text == "/start":
                    send_vk_message(user_id, "Привет 👋 Бот работает!")
                elif text == "/help":
                    send_vk_message(user_id, "/start — проверить запуск\n/help — помощь")
                else:
                    send_vk_message(user_id, "Получил: " + text)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")


server = HTTPServer(("0.0.0.0", PORT), Handler)
print(f"Server started on port {PORT}")
server.serve_forever()
