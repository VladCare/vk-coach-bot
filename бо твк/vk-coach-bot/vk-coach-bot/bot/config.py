from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    vk_token: str
    openai_api_key: str | None
    openai_model: str
    db_path: Path
    export_dir: Path
    default_timezone: str
    default_morning_time: str
    default_midday_time: str
    default_evening_time: str


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


def load_settings() -> Settings:
    vk_token = os.getenv("VK_TOKEN", "").strip()
    if not vk_token:
        raise ConfigError(
            "Переменная VK_TOKEN не задана. Создай ключ доступа сообщества VK и положи токен в .env"
        )

    db_path = Path(os.getenv("DB_PATH", "data/study_tracker.db")).expanduser()
    export_dir = Path(os.getenv("EXPORT_DIR", "exports")).expanduser()

    db_path.parent.mkdir(parents=True, exist_ok=True)
    export_dir.mkdir(parents=True, exist_ok=True)

    return Settings(
        vk_token=vk_token,
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip() or None,
        openai_model=os.getenv("OPENAI_MODEL", "gpt-5-mini").strip() or "gpt-5-mini",
        db_path=db_path,
        export_dir=export_dir,
        default_timezone=os.getenv("DEFAULT_TIMEZONE", "Europe/Amsterdam").strip() or "Europe/Amsterdam",
        default_morning_time=os.getenv("DEFAULT_MORNING_TIME", "08:00").strip() or "08:00",
        default_midday_time=os.getenv("DEFAULT_MIDDAY_TIME", "14:00").strip() or "14:00",
        default_evening_time=os.getenv("DEFAULT_EVENING_TIME", "20:30").strip() or "20:30",
    )
