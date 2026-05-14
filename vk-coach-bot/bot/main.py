from __future__ import annotations

import html
import logging
import re
from datetime import date

from dotenv import load_dotenv
from vkbottle.bot import Bot, Message

from .ai_service import AIService
from .config import ConfigError, load_settings
from .db import Database
from .formatters import format_plan_table, progress_summary

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

try:
    settings = load_settings()
except ConfigError as exc:
    raise SystemExit(str(exc)) from exc

bot = Bot(token=settings.vk_token)
db = Database(settings.db_path)
ai = AIService(api_key=settings.openai_api_key, model=settings.openai_model)


HELP_TEXT = """
Привет 👋 Я AI-коуч для учебы, задач и продуктивности.

Команды:
/start — начать
/help — помощь
/add текст задачи — добавить задачу
/tasks — план на сегодня
/done ID — отметить задачу выполненной
/skip ID — отложить задачу
/delete ID — удалить задачу
/analysis — AI-анализ дня
/profile био | хобби1, хобби2 — заполнить профиль

Можно просто написать вопрос обычным сообщением — я отвечу как коуч.
""".strip()


def today() -> str:
    return date.today().isoformat()


def clean_message(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text or "")
    return html.unescape(text).strip()


async def ensure_vk_user(message: Message) -> dict:
    # В базе поле пока называется telegram_id, но мы используем там VK user_id.
    return await db.ensure_user(
        telegram_id=int(message.from_id),
        full_name=str(message.from_id),
        username=None,
        timezone=settings.default_timezone,
        morning_time=settings.default_morning_time,
        midday_time=settings.default_midday_time,
        evening_time=settings.default_evening_time,
    )


async def send_long(message: Message, text: str) -> None:
    text = clean_message(text)
    if not text:
        text = "Пустой ответ. Попробуй еще раз."
    # VK обычно спокойно принимает длинные сообщения, но режем безопасно.
    limit = 3500
    for start in range(0, len(text), limit):
        await message.answer(text[start : start + limit])


@bot.on.message(text=["/start", "Начать", "начать"])
async def start(message: Message) -> None:
    await db.init()
    await ensure_vk_user(message)
    await message.answer(HELP_TEXT)


@bot.on.message(text=["/help", "помощь", "Помощь"])
async def help_handler(message: Message) -> None:
    await message.answer(HELP_TEXT)


@bot.on.message(text=["/tasks", "задачи", "Задачи"])
async def tasks_handler(message: Message) -> None:
    await db.init()
    await ensure_vk_user(message)
    tasks = await db.get_tasks_for_day(int(message.from_id), today())
    await send_long(message, format_plan_table(tasks) + "\n\n" + progress_summary(tasks))


@bot.on.message(text=["/analysis", "анализ", "Анализ"])
async def analysis_handler(message: Message) -> None:
    await db.init()
    user = await ensure_vk_user(message)
    tasks = await db.get_tasks_for_day(int(message.from_id), today())
    checkins = await db.get_checkins_for_day(int(message.from_id), today())
    history = await db.get_recent_history(int(message.from_id), days=7)
    result = await ai.daily_analysis(user, tasks, checkins, history)
    await db.save_ai_analysis(int(message.from_id), today(), result)
    await send_long(message, result)


@bot.on.message()
async def message_handler(message: Message) -> None:
    await db.init()
    user = await ensure_vk_user(message)
    text = (message.text or "").strip()

    if not text:
        await message.answer("Напиши текстом задачу или вопрос.")
        return

    lower = text.lower()

    if lower.startswith("/add "):
        title = text[5:].strip()
        if not title:
            await message.answer("Напиши так: /add подготовиться к математике 40 мин")
            return
        task_id = await db.add_task(
            telegram_id=int(message.from_id),
            day=today(),
            title=title,
            priority=2,
            duration_minutes=None,
            note=None,
        )
        await message.answer(f"Добавил задачу #{task_id}: {title}")
        return

    if lower.startswith("/done ") or lower.startswith("/skip ") or lower.startswith("/delete "):
        parts = text.split(maxsplit=1)
        if len(parts) < 2 or not parts[1].strip().isdigit():
            await message.answer("Укажи ID задачи. Например: /done 3")
            return
        task_id = int(parts[1].strip())
        task = await db.get_task(task_id)
        if not task:
            await message.answer("Задача не найдена.")
            return
        if lower.startswith("/done "):
            await db.update_task_status(task_id, "done")
            await message.answer(f"Готово ✅ Задача #{task_id} выполнена.")
        elif lower.startswith("/skip "):
            await db.update_task_status(task_id, "skipped")
            await message.answer(f"Ок, задача #{task_id} отложена.")
        else:
            await db.delete_task(task_id)
            await message.answer(f"Удалил задачу #{task_id}.")
        return

    if lower.startswith("/profile "):
        raw = text[len("/profile ") :].strip()
        bio, _, hobbies_raw = raw.partition("|")
        hobbies = [item.strip() for item in hobbies_raw.split(",") if item.strip()]
        await db.update_profile(
            telegram_id=int(message.from_id),
            bio=bio.strip(),
            hobbies=hobbies,
            timezone=settings.default_timezone,
            morning_time=settings.default_morning_time,
            midday_time=settings.default_midday_time,
            evening_time=settings.default_evening_time,
        )
        await message.answer("Профиль сохранил ✅")
        return

    tasks = await db.get_tasks_for_day(int(message.from_id), today())
    history = await db.get_recent_history(int(message.from_id), days=7)
    result = await ai.coach_reply(
        user=user,
        today_tasks=tasks,
        recent_history=history,
        question=text,
    )
    await send_long(message, result)


if __name__ == "__main__":
    bot.run_forever()
