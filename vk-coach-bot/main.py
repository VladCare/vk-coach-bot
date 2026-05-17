import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from dotenv import load_dotenv
from vkbottle.bot import Bot, Message

load_dotenv()

VK_TOKEN = os.getenv("VK_TOKEN")
PORT = int(os.getenv("PORT", 10000))

if not VK_TOKEN:
    raise RuntimeError("VK_TOKEN is not set")


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"VK bot is running")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()


def run_health_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    server.serve_forever()


bot = Bot(token=VK_TOKEN)


@bot.on.message(text=["/start", "Начать"])
async def start(message: Message):
    await message.answer("Привет 👋 Бот работает!")


@bot.on.message(text="/help")
async def help_cmd(message: Message):
    await message.answer(
        "/start — проверить запуск\n"
        "/help — помощь"
    )


@bot.on.message()
async def echo(message: Message):
    await message.answer("Получил: " + (message.text or ""))


if __name__ == "__main__":
    threading.Thread(target=run_health_server, daemon=True).start()
    bot.run_forever()
