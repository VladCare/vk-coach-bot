from __future__ import annotations

from collections import Counter
from typing import Any

try:
    from openai import AsyncOpenAI
except Exception:  # pragma: no cover
    AsyncOpenAI = None  # type: ignore[assignment]

from .formatters import PRIORITY_LABELS, format_hobbies


class AIService:
    def __init__(self, api_key: str | None, model: str) -> None:
        self.model = model
        self.enabled = bool(api_key and AsyncOpenAI is not None)
        self.client = AsyncOpenAI(api_key=api_key) if self.enabled else None

    async def daily_analysis(
        self,
        user: dict[str, Any],
        today_tasks: list[dict[str, Any]],
        today_checkins: list[dict[str, Any]],
        recent_history: dict[str, list[dict[str, Any]]],
    ) -> str:
        if not self.enabled or not self.client:
            return self._fallback_analysis(user, today_tasks, today_checkins, recent_history)

        prompt = self._build_daily_analysis_prompt(user, today_tasks, today_checkins, recent_history)
        response = await self.client.responses.create(
            model=self.model,
            instructions=(
                "Ты личный учебный и продуктивный коуч в Telegram. "
                "Отвечай на русском. Пиши практично, не занудно. "
                "Анализируй пользователя как живого человека: учитывай его биографию, увлечения, "
                "прошлые срывы и текущую нагрузку. "
                "Формат ответа: 1) главный фокус дня, 2) риски, 3) что изменить в плане, "
                "4) короткое мотивирующее сообщение. Без длинных вступлений."
            ),
            input=prompt,
            max_output_tokens=500,
        )
        return (response.output_text or "").strip() or self._fallback_analysis(
            user, today_tasks, today_checkins, recent_history
        )

    async def coach_reply(
        self,
        user: dict[str, Any],
        today_tasks: list[dict[str, Any]],
        recent_history: dict[str, list[dict[str, Any]]],
        question: str,
    ) -> str:
        if not self.enabled or not self.client:
            return self._fallback_coach_reply(user, today_tasks, recent_history, question)

        prompt = self._build_coach_prompt(user, today_tasks, recent_history, question)
        response = await self.client.responses.create(
            model=self.model,
            instructions=(
                "Ты личный AI-наставник для школьника/студента и работающего человека. "
                "Отвечай на русском. Ответ должен быть конкретным: короткий разбор, затем план на 3-5 шагов. "
                "Не морализируй. Делай советы реалистичными."
            ),
            input=prompt,
            max_output_tokens=500,
        )
        return (response.output_text or "").strip() or self._fallback_coach_reply(
            user, today_tasks, recent_history, question
        )

    @staticmethod
    def _build_daily_analysis_prompt(
        user: dict[str, Any],
        today_tasks: list[dict[str, Any]],
        today_checkins: list[dict[str, Any]],
        recent_history: dict[str, list[dict[str, Any]]],
    ) -> str:
        profile = (
            f"Имя: {user.get('full_name') or 'не указано'}\n"
            f"Биография: {user.get('bio') or 'не указана'}\n"
            f"Увлечения: {format_hobbies(user.get('hobbies', []))}\n"
            f"Часовой пояс: {user.get('timezone')}\n"
        )

        tasks_text = "\n".join(
            f"- {task['title']} | приоритет {PRIORITY_LABELS.get(task.get('priority', 2), 'средний')} | "
            f"статус {task.get('status')} | длительность {task.get('duration_minutes') or 'не указана'}"
            for task in today_tasks
        ) or "- задач пока нет"

        checkins_text = "\n".join(
            f"- {checkin['kind']}: {checkin['summary']}" for checkin in today_checkins
        ) or "- чек-инов нет"

        last_tasks = recent_history.get("tasks", [])
        counter = Counter(task.get("status", "pending") for task in last_tasks)
        recent_summary = (
            f"За последние дни задач: {len(last_tasks)}\n"
            f"Выполнено: {counter.get('done', 0)}\n"
            f"Отложено: {counter.get('skipped', 0)}\n"
            f"Незавершено: {counter.get('pending', 0)}"
        )

        return (
            "Профиль пользователя:\n"
            f"{profile}\n"
            "Сегодняшние задачи:\n"
            f"{tasks_text}\n\n"
            "Сегодняшние заметки пользователя:\n"
            f"{checkins_text}\n\n"
            "История продуктивности:\n"
            f"{recent_summary}\n\n"
            "Сделай анализ так, будто ты знаешь пользователя лично и видишь его сильные стороны и паттерны срыва."
        )

    @staticmethod
    def _build_coach_prompt(
        user: dict[str, Any],
        today_tasks: list[dict[str, Any]],
        recent_history: dict[str, list[dict[str, Any]]],
        question: str,
    ) -> str:
        tasks_text = "\n".join(
            f"- {task['title']} ({task.get('status')}, приоритет {task.get('priority')})" for task in today_tasks
        ) or "- задач на сегодня нет"

        last_tasks = recent_history.get("tasks", [])[-10:]
        history_text = "\n".join(
            f"- {task['day']}: {task['title']} -> {task['status']}" for task in last_tasks
        ) or "- история пустая"

        return (
            f"Пользователь: {user.get('full_name') or 'не указано'}\n"
            f"Биография: {user.get('bio') or 'не указана'}\n"
            f"Увлечения: {format_hobbies(user.get('hobbies', []))}\n\n"
            f"План на сегодня:\n{tasks_text}\n\n"
            f"Недавняя история:\n{history_text}\n\n"
            f"Вопрос пользователя: {question.strip()}"
        )

    @staticmethod
    def _fallback_analysis(
        user: dict[str, Any],
        today_tasks: list[dict[str, Any]],
        today_checkins: list[dict[str, Any]],
        recent_history: dict[str, list[dict[str, Any]]],
    ) -> str:
        hobbies = format_hobbies(user.get("hobbies", []))
        pending = [task for task in today_tasks if task.get("status") == "pending"]
        done = [task for task in today_tasks if task.get("status") == "done"]
        high_priority = [task for task in pending if task.get("priority") == 3]
        last_tasks = recent_history.get("tasks", [])
        counter = Counter(task.get("status", "pending") for task in last_tasks)
        total = max(len(last_tasks), 1)
        completion_rate = round(counter.get("done", 0) / total * 100)
        latest_checkin = today_checkins[-1]["summary"] if today_checkins else "ты ещё не писал промежуточный отчёт"

        focus = high_priority[0]["title"] if high_priority else (pending[0]["title"] if pending else "закрыть день и подвести итог")
        risk = (
            "план перегружен" if len(pending) >= 5 else "есть риск потерять темп после первой сложной задачи"
            if pending else "риск скорее в том, что ты недооценишь уже сделанный объём"
        )
        tweak = (
            "разбей первую сложную задачу на 2 коротких спринта по 25 минут"
            if high_priority
            else "выбери 1 главную задачу и не распыляйся"
        )
        return (
            f"1) Главный фокус дня: <b>{focus}</b>.\n"
            f"2) Риск: <b>{risk}</b>.\n"
            f"3) Что изменить: {tweak}. Учитывая твои увлечения ({hobbies}), полезно добавить награду после ключевого блока работы.\n"
            f"4) По истории у тебя примерно <b>{completion_rate}%</b> завершения задач. Последняя заметка: “{latest_checkin}”.\n"
            f"Мотивация: ты уже закрыл <b>{len(done)}</b> задач сегодня — держи ритм, но не делай план красивее, чем он реалистичен."
        )

    @staticmethod
    def _fallback_coach_reply(
        user: dict[str, Any],
        today_tasks: list[dict[str, Any]],
        recent_history: dict[str, list[dict[str, Any]]],
        question: str,
    ) -> str:
        pending = [task["title"] for task in today_tasks if task.get("status") == "pending"]
        hobbies = format_hobbies(user.get("hobbies", []))
        return (
            f"Разбор: ты спросил про “{question.strip()}”. Сейчас у тебя в фокусе: "
            f"{', '.join(pending[:3]) if pending else 'нет активных задач в плане'}.\n\n"
            "План на 3 шага:\n"
            "1) Выбери один ближайший результат на ближайшие 30-40 минут.\n"
            "2) Убери всё лишнее и включи таймер.\n"
            "3) После блока напиши мне короткий отчёт — что сделал и где застрял.\n\n"
            f"Подстройка под тебя: используй свои интересы ({hobbies}) как награду после завершения важного куска работы."
        )
