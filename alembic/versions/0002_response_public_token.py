"""add responses.public_token

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-23
"""
import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) add nullable, 2) backfill existing rows, 3) enforce NOT NULL + unique.
    op.add_column("responses", sa.Column("public_token", sa.String(length=32), nullable=True))

    conn = op.get_bind()
    ids = conn.execute(sa.text("SELECT id FROM responses WHERE public_token IS NULL")).fetchall()
    for (rid,) in ids:
        conn.execute(
            sa.text("UPDATE responses SET public_token = :t WHERE id = :id"),
            {"t": uuid.uuid4().hex, "id": rid},
        )

    op.alter_column("responses", "public_token", existing_type=sa.String(length=32), nullable=False)
    op.create_index("ix_responses_public_token", "responses", ["public_token"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_responses_public_token", table_name="responses")
    op.drop_column("responses", "public_token")
