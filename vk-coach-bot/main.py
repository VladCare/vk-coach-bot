import os
from dotenv import load_dotenv
from vkbottle.bot import Bot, Message

load_dotenv()

VK_TOKEN = os.getenv("VK_TOKEN")

if not VK_TOKEN:
    raise RuntimeError("VK_TOKEN is not set")

bot = Bot(token=VK_TOKEN)


@bot.on.message(text=["/start", "Начать"])
async def start(message: Message):
    await message.answer("Привет 👋 Бот работает.")


@bot.on.message(text="/help")
async def help_cmd(message: Message):
    await message.answer("/start — проверить запуск\n/help — помощь")


@bot.on.message()
async def echo(message: Message):
    await message.answer("Получил: " + (message.text or ""))


bot.run_forever()
