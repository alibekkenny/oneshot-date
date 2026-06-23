"""ORM models. Schema is owned by Alembic migrations (alembic/versions)."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def _new_token() -> str:
    return uuid.uuid4().hex


class Response(Base):
    """One completed run through the wizard."""

    __tablename__ = "responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Opaque, unguessable handle the browser keeps so she can revisit her plan.
    # Random (not the sequential id) so a later visitor can't enumerate responses.
    public_token: Mapped[str] = mapped_column(
        String(32), unique=True, index=True, nullable=False, default=_new_token
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    girl_name: Mapped[str] = mapped_column(String(120), nullable=False)
    # Multi-selects, stored as JSON arrays of the chosen labels.
    entertainment: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    eating: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    drinking: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    proposed_when: Mapped[str | None] = mapped_column(String(200), nullable=True)
    answer: Mapped[str] = mapped_column(String(20), nullable=False)  # "yes" | "no"
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(400), nullable=True)


class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
