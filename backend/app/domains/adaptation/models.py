import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.domains.adaptation.enums import AdjustmentReason


class LoadAdjustment(Base):
    """One decision of the adaptation: the load suggested for an exercise from now on.

    Append-only - the newest row for (user, exercise) is the current suggestion, the
    older rows are its history.
    """

    __tablename__ = "load_adjustments"
    __table_args__ = (
        Index(
            "ix_load_adjustments_user_id_exercise_id_created_at",
            "user_id",
            "exercise_id",
            "created_at",
        ),
        CheckConstraint("weight_kg >= 0", name="weight_non_negative"),
        CheckConstraint("previous_weight_kg >= 0", name="previous_weight_non_negative"),
        CheckConstraint("e1rm_kg > 0", name="e1rm_positive"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="RESTRICT"), index=True
    )
    workout_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("workout_logs.id", ondelete="SET NULL"), index=True
    )
    previous_weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    weight_kg: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    e1rm_kg: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    reason: Mapped[AdjustmentReason] = mapped_column(
        Enum(
            AdjustmentReason,
            name="adjustment_reason",
            values_callable=lambda e: [member.value for member in e],
        )
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
