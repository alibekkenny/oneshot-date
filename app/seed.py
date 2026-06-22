"""Seed the admin user from ADMIN_USERNAME / ADMIN_PASSWORD.

Runs on startup (see app/main.py) and is idempotent: it only creates the admin
if one with that username doesn't already exist. Can also be run standalone:

    python -m app.seed
"""
import logging

from .config import get_settings
from .db import SessionLocal
from .models import AdminUser
from .security import hash_password

logger = logging.getLogger("oneshot.seed")


def seed_admin() -> None:
    settings = get_settings()
    if not settings.admin_password:
        logger.warning("ADMIN_PASSWORD not set — skipping admin seed.")
        return

    db = SessionLocal()
    try:
        existing = db.query(AdminUser).filter_by(username=settings.admin_username).first()
        if existing is not None:
            return
        db.add(
            AdminUser(
                username=settings.admin_username,
                password_hash=hash_password(settings.admin_password),
            )
        )
        db.commit()
        logger.info("Seeded admin user %r.", settings.admin_username)
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_admin()
