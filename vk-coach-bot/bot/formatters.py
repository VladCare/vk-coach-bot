from __future__ import annotations

from collections import Counter
from typing import Iterable


PRIORITY_LABELS = {
    1: "низкий",
    2: "средний",
    3: "высокий",
}

STATUS_ICON = {
    "pending": "⏳",
    "done": "✅",
    "skipped": "⏭️",
}


def shorten(text: str, width: int) -> str:
    clean = (text or "").replace("\n", " ").strip()
    if len(clean) <= width:
        return clean.ljust(width)
    if width <= 1:
        return clean[:width]
    return (clean[: width - 1] + "…")


def format_plan_table(tasks: list[dict]) -> str:
    if not tasks:
        return "<b>На сегодня задач пока нет.</b>\nНажми «➕ Добавить задачу», и я соберу тебе план."

    lines = []
    header = f"{'#':<2} {'P':<1} {'Задача':<28} {'Мин':>4} {'Статус':<6}"
    sep = "-" * len(header)
    lines.append(header)
    lines.append(sep)
    for idx, task in enumerate(tasks, start=1):
        priority = str(task.get("priority", 2))
        title = shorten(task.get("title", ""), 28)
        duration = str(task.get("duration_minutes") or "-")
        status = STATUS_ICON.get(task.get("status", "pending"), "⏳")
        lines.append(f"{idx:<2} {priority:<1} {title} {duration:>4} {status:<6}")

    return "<b>План на день</b>\n<pre>" + "\n".join(lines) + "</pre>"


def progress_summary(tasks: list[dict]) -> str:
    if not tasks:
        return "План на день пока пустой."

    counter = Counter(task.get("status", "pending") for task in tasks)
    total = len(tasks)
    done = counter.get("done", 0)
    pending = counter.get("pending", 0)
    skipped = counter.get("skipped", 0)
    percent = round((done / total) * 100) if total else 0
    return (
        f"Всего задач: <b>{total}</b>\n"
        f"✅ Выполнено: <b>{done}</b>\n"
        f"⏳ В процессе: <b>{pending}</b>\n"
        f"⏭️ Отложено: <b>{skipped}</b>\n"
        f"📈 Прогресс: <b>{percent}%</b>"
    )


def format_task_details(task: dict) -> str:
    duration = task.get("duration_minutes")
    duration_text = f"{duration} мин" if duration else "не указано"
    note = task.get("note") or "—"
    return (
        f"<b>{task.get('title')}</b>\n"
        f"Приоритет: <b>{PRIORITY_LABELS.get(task.get('priority'), 'средний')}</b>\n"
        f"Длительность: <b>{duration_text}</b>\n"
        f"Статус: <b>{task.get('status')}</b>\n"
        f"Комментарий: {note}"
    )


def format_hobbies(hobbies: Iterable[str]) -> str:
    values = [item.strip() for item in hobbies if item and item.strip()]
    return ", ".join(values) if values else "не указаны"
