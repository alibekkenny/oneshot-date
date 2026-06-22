"""Send a notification to the owner via the Telegram Bot API.

No-ops (with a warning) when the bot isn't configured, so local dev works
without Telegram credentials.
"""
import logging

import httpx

from .config import get_settings

logger = logging.getLogger("oneshot.telegram")


def send_message(text: str) -> bool:
    settings = get_settings()
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        logger.warning("Telegram not configured; skipping message:\n%s", text)
        return False

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    try:
        resp = httpx.post(
            url,
            json={
                "chat_id": settings.telegram_chat_id,
                "text": text,
                "parse_mode": "HTML",
            },
            timeout=10,
        )
        resp.raise_for_status()
        return True
    except Exception as exc:  # never let a notification failure break the response flow
        logger.exception("Failed to send Telegram message: %s", exc)
        return False
