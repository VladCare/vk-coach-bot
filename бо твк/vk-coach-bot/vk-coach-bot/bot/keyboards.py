from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


BTN_ADD = "➕ Добавить задачу"
BTN_PLAN = "📋 План на сегодня"
BTN_DONE = "✅ Отметить выполнение"
BTN_AI = "🧠 AI-анализ"
BTN_COACH = "💬 AI-коуч"
BTN_EXPORT = "📤 Экспорт"
BTN_SETTINGS = "⚙️ Настройки"
BTN_CANCEL = "❌ Отмена"


PRIORITY_LOW = "1 — Низкий"
PRIORITY_MED = "2 — Средний"
PRIORITY_HIGH = "3 — Высокий"


SCHEDULE_MORNING = "schedule:morning"
SCHEDULE_MIDDAY = "schedule:midday"
SCHEDULE_EVENING = "schedule:evening"
SCHEDULE_TZ = "schedule:timezone"


TIMEZONE_OPTIONS = [
    ("Europe/Amsterdam", "🇳🇱 Amsterdam"),
    ("Europe/Moscow", "🇷🇺 Moscow"),
    ("Europe/Berlin", "🇩🇪 Berlin"),
    ("Asia/Almaty", "🇰🇿 Almaty"),
]


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(BTN_ADD), KeyboardButton(BTN_PLAN)],
            [KeyboardButton(BTN_DONE), KeyboardButton(BTN_AI)],
            [KeyboardButton(BTN_COACH), KeyboardButton(BTN_EXPORT)],
            [KeyboardButton(BTN_SETTINGS)],
        ],
        resize_keyboard=True,
    )


def cancel_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([[KeyboardButton(BTN_CANCEL)]], resize_keyboard=True, one_time_keyboard=True)


def priority_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(PRIORITY_LOW), KeyboardButton(PRIORITY_MED), KeyboardButton(PRIORITY_HIGH)],
            [KeyboardButton(BTN_CANCEL)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def yes_no_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[KeyboardButton("Да"), KeyboardButton("Нет")], [KeyboardButton(BTN_CANCEL)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def task_action_keyboard(tasks: list[dict]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for idx, task in enumerate(tasks, start=1):
        rows.append(
            [
                InlineKeyboardButton(f"✅ {idx}", callback_data=f"done:{task['id']}"),
                InlineKeyboardButton(f"⏭️ {idx}", callback_data=f"skip:{task['id']}"),
                InlineKeyboardButton(f"🗑️ {idx}", callback_data=f"delete:{task['id']}"),
            ]
        )
    return InlineKeyboardMarkup(rows)


def quick_plan_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("➕ Добавить задачу", callback_data="open:add")],
            [InlineKeyboardButton("📋 Открыть план", callback_data="open:plan")],
            [InlineKeyboardButton("🧠 Разобрать день", callback_data="open:analysis")],
        ]
    )


def settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🌅 Утреннее напоминание", callback_data=SCHEDULE_MORNING)],
            [InlineKeyboardButton("☀️ Дневное напоминание", callback_data=SCHEDULE_MIDDAY)],
            [InlineKeyboardButton("🌙 Вечернее напоминание", callback_data=SCHEDULE_EVENING)],
            [InlineKeyboardButton("🕒 Часовой пояс", callback_data=SCHEDULE_TZ)],
        ]
    )


def timezone_keyboard() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(label, callback_data=f"tz:{zone}")] for zone, label in TIMEZONE_OPTIONS]
    return InlineKeyboardMarkup(rows)
