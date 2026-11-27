"""movement patterns for catv2

Revision ID: 76e4bbb01245
Revises: 70a474fef30d
Create Date: 2026-11-24 20:53:09.222602

"""
from collections.abc import Sequence

from alembic import op

revision: str = "c4f1e2a9b7d3"
down_revision: str | Sequence[str] | None = "70a474fef30d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NEW_PATTERNS = (
    "shoulder_flexion",
    "shoulder_extension",
    "scapular_elevation",
    "hip_adduction",
    "hip_abduction",
    "core_rotation",
    "core_anti_rotation",
)


def upgrade() -> None:
    for value in NEW_PATTERNS:
        op.execute(f"ALTER TYPE movement_pattern ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    # Postgres cannot drop a value from an enum type. The extra values are harmless
    # for the older code as long as no exercise uses them (seed catalog v1 again).
    pass