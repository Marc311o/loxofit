"""What the user actually did: workouts, the exercises in them and their sets.

A workout copies the prescription it was started from (targets, the suggested load,
the session name, the body weight), so that its history stays true when the plan is
edited or deleted later.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    UUID,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.domains.workouts.enums import WorkoutStatus


class WorkoutLog(Base):
    __tablename__ = "workout_logs"
    __table_args__ = (
        # One workout at a time per user - also when two starts come at once.
        Index(
            "uq_workout_logs_one_in_progress_per_user",
            "user_id",
            unique=True,
            postgresql_where=text("status = 'in_progress'"),
        ),
        Index("ix_workout_logs_user_id_started_at", "user_id", "started_at"),
        CheckConstraint("session_rpe BETWEEN 1 AND 10", name="session_rpe_range"),
        CheckConstraint(
            "finished_at IS NULL OR finished_at >= started_at", name="finished_after_started"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    plan_session_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("plan_sessions.id", ondelete="SET NULL"), index=True
    )
    session_name: Mapped[str] = mapped_column(String(50))
    status: Mapped[WorkoutStatus] = mapped_column(
        Enum(
            WorkoutStatus,
            name="workout_status",
            values_callable=lambda e: [member.value for member in e],
        ),
        default=WorkoutStatus.IN_PROGRESS,
        server_default=WorkoutStatus.IN_PROGRESS.value,
    )
    body_weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    session_rpe: Mapped[int | None] = mapped_column(SmallInteger)
    notes: Mapped[str | None] = mapped_column(String(500))

    exercises: Mapped[list["LoggedExercise"]] = relationship(
        back_populates="workout",
        order_by="LoggedExercise.position",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="raise",
    )


class LoggedExercise(Base):
    __tablename__ = "logged_exercises"
    __table_args__ = (
        UniqueConstraint("workout_id", "position", name="uq_logged_exercises_workout_id_position"),
        CheckConstraint("position >= 1", name="position_positive"),
        CheckConstraint("target_sets BETWEEN 1 AND 10", name="target_sets_range"),
        CheckConstraint(
            "target_rep_min IS NULL OR target_rep_max IS NULL OR target_rep_min <= target_rep_max",
            name="target_rep_range_order",
        ),
        CheckConstraint("target_rir BETWEEN 0 AND 5", name="target_rir_range"),
        CheckConstraint("suggested_weight_kg >= 0", name="suggested_weight_non_negative"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    workout_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workout_logs.id", ondelete="CASCADE"))
    prescribed_exercise_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("prescribed_exercises.id", ondelete="SET NULL"), index=True
    )
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="RESTRICT"), index=True
    )
    position: Mapped[int] = mapped_column(SmallInteger)
    target_sets: Mapped[int] = mapped_column(SmallInteger)
    target_rep_min: Mapped[int | None] = mapped_column(SmallInteger)
    target_rep_max: Mapped[int | None] = mapped_column(SmallInteger)
    target_rir: Mapped[int] = mapped_column(SmallInteger)
    suggested_weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))

    workout: Mapped["WorkoutLog"] = relationship(back_populates="exercises", lazy="raise")
    sets: Mapped[list["LoggedSet"]] = relationship(
        back_populates="exercise",
        order_by="LoggedSet.set_number",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="raise",
    )


class LoggedSet(Base):
    """A working set. For bodyweight exercises `weight_kg` is the added load (0 = none)."""

    __tablename__ = "logged_sets"
    __table_args__ = (
        UniqueConstraint(
            "logged_exercise_id",
            "set_number",
            name="uq_logged_sets_logged_exercise_id_set_number",
        ),
        CheckConstraint("set_number >= 1", name="set_number_positive"),
        CheckConstraint("weight_kg >= 0", name="weight_non_negative"),
        CheckConstraint("reps BETWEEN 0 AND 100", name="reps_range"),
        CheckConstraint("rir BETWEEN 0 AND 5", name="rir_range"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    logged_exercise_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("logged_exercises.id", ondelete="CASCADE")
    )
    set_number: Mapped[int] = mapped_column(SmallInteger)
    weight_kg: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    reps: Mapped[int] = mapped_column(SmallInteger)
    rir: Mapped[int | None] = mapped_column(SmallInteger)
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    exercise: Mapped["LoggedExercise"] = relationship(back_populates="sets", lazy="raise")
