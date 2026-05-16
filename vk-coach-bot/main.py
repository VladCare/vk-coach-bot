import os
from dotenv import load_dotenv
from vkbottle.bot import Bot, Message

load_dotenv()

VK_TOKEN = os.getenv("VK_TOKEN")
bot = Bot(token=VK_TOKEN)


@bot.on.message(text=["/start", "Начать"])
async def start(message: Message):
    await message.answer(
        "Привет 👋\n\n"
        "Я AI-коуч для учебы.\n"
        "Пока работаю в тестовом режиме.\n\n"
        "Напиши /help"
    )


@bot.on.message(text="/help")
async def help_cmd(message: Message):
    await message.answer(
        "Команды:\n"
        "/start — запуск\n"
        "/help — помощь\n\n"
        "Скоро добавим задачи и AI."
    )


@bot.on.message()
async def echo(message: Message):
    await message.answer(
        "Я получил сообщение:\n"
        f"{message.text}"
    )


if __name__ == "__main__":
    bot.run_forever()
