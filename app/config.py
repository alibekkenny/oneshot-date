"""Application settings, loaded from environment / .env (see .env.example)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Who this whole thing is for. Shown all over the page.
    girl_name: str = "Aimaral"

    # SQLAlchemy URL. For docker-compose this is overridden to point at the "db" host.
    database_url: str = "postgresql+psycopg2://oneshot:oneshot@localhost:5432/oneshot"

    # Telegram: created via @BotFather; chat id from @userinfobot.
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # Admin panel. The admin user is seeded from these on startup (see app/seed.py).
    admin_username: str = "admin"
    admin_password: str = ""
    session_secret: str = "dev-insecure-secret-change-me"

    app_title: str = "A little question"


@lru_cache
def get_settings() -> Settings:
    return Settings()
