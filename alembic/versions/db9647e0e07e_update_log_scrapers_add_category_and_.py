"""update log scrapers, add category and value is now a json.

Revision ID: db9647e0e07e
Revises: f3025f4c7f60
Create Date: 2026-09-13 16:58:37.065187

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'db9647e0e07e'
down_revision: Union[str, Sequence[str], None] = 'f3025f4c7f60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DELETE FROM metrics")

    metric_category_enum = postgresql.ENUM(
        "RECUPERATION",
        "EXPLORATION",
        name="metriccategory",
    )
    metric_category_enum.create(op.get_bind(), checkfirst=True)
    
    op.execute("ALTER TYPE metrictype ADD VALUE IF NOT EXISTS 'TABLE';")

    op.add_column("metrics", sa.Column("category", metric_category_enum, nullable=True))
    op.alter_column(
        "metrics",
        "value",
        existing_type=sa.DOUBLE_PRECISION(precision=53),
        type_=sa.JSON(),
        postgresql_using="to_json(value)",
        nullable=True,
    )


def downgrade() -> None:
    op.execute("DELETE FROM metrics")
    op.alter_column(
        "metrics",
        "value",
        existing_type=sa.JSON(),
        type_=sa.DOUBLE_PRECISION(precision=53),
        postgresql_using="(value->>'value')::double precision",
        nullable=False,
    )
    op.drop_column("metrics", "category")
    postgresql.ENUM(name="metriccategory").drop(op.get_bind(), checkfirst=True)