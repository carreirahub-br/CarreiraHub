"""add external_url to jobs

Revision ID: d7390d14236a
Revises: 0001
Create Date: 2026-11-02 00:50:29.761530
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



revision: str = 'd7390d14236a'
down_revision: Union[str, Sequence[str], None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("external_url", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("jobs", "external_url")
