import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    UUID,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.domains.generator.enums import GenerationStatus


class GenerationRun(Base):
    """One run of the plan generator: what was asked, how it went and what came out.

    The request and the seed reproduce the run (with the same catalog and config).
    `result` holds the base week as [[[exercise_id, sets], ...], ...] - one list per
    session, in the order of the request's sessions; `history` the best score so far
    at every improvement as [[evaluations, score], ...].
    """

    __tablename__ = "generation_runs"
    __table_args__ = (
        # One generation at a time per user - also when two requests come at once.
        Index(
            "uq_generation_runs_one_active_per_user",
            "user_id",
            unique=True,
            postgresql_where=text("status IN ('queued', 'running')"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    config_id: Mapped[int] = mapped_column(ForeignKey("model_configs.id", ondelete="RESTRICT"))
    plan_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("plans.id", ondelete="SET NULL"))
    status: Mapped[GenerationStatus] = mapped_column(
        Enum(
            GenerationStatus,
            name="generation_status",
            values_callable=lambda e: [member.value for member in e],
        ),
        default=GenerationStatus.QUEUED,
        server_default=GenerationStatus.QUEUED.value,
    )
    params: Mapped[dict[str, Any]] = mapped_column(JSONB)
    seed: Mapped[int] = mapped_column(Integer)
    algorithm: Mapped[str] = mapped_column(String(30))
    budget: Mapped[int] = mapped_column(Integer)

    evaluations: Mapped[int | None] = mapped_column(Integer)
    score: Mapped[float | None] = mapped_column(Float)
    max_score: Mapped[float | None] = mapped_column(Float)
    result: Mapped[list[list[list[int]]] | None] = mapped_column(JSONB)
    history: Mapped[list[list[float]] | None] = mapped_column(JSONB)
    error: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
