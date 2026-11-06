import uuid
from datetime import datetime

from sqlalchemy import (
    UUID,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    UniqueConstraint,
    false,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.domains.plans.enums import PlanStatus


class Plan(Base):
    __tablename__ = "plans"
    __table_args__ = (
        CheckConstraint("num_weeks BETWEEN 2 AND 12", name="num_weeks_range"),
        Index(
            "uq_plans_single_active_per_user",
            "user_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    config_id: Mapped[int] = mapped_column(ForeignKey("model_configs.id", ondelete="RESTRICT"))
    name: Mapped[str] = mapped_column(String(100))
    status: Mapped[PlanStatus] = mapped_column(
        Enum(
            PlanStatus,
            name="plan_status",
            values_callable=lambda e: [member.value for member in e],
        ),
        default=PlanStatus.DRAFT,
        server_default=PlanStatus.DRAFT.value,
    )
    num_weeks: Mapped[int] = mapped_column(SmallInteger, default=5, server_default="5")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    weeks: Mapped[list["PlanWeek"]] = relationship(
        back_populates="plan",
        order_by="PlanWeek.week_number",
        cascade="all, delete-orphan",
        lazy="raise",
    )
    muscle_targets: Mapped[list["PlanMuscleTarget"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan", lazy="raise"
    )


class PlanWeek(Base):
    __tablename__ = "plan_weeks"
    __table_args__ = (
        UniqueConstraint("plan_id", "week_number", name="uq_plan_weeks_plan_id_week_number"),
        CheckConstraint("week_number >= 1", name="week_number_positive"),
        CheckConstraint("rir BETWEEN 0 AND 5", name="rir_range"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("plans.id", ondelete="CASCADE"))
    week_number: Mapped[int] = mapped_column(SmallInteger)
    rir: Mapped[int] = mapped_column(SmallInteger)
    is_deload: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())

    plan: Mapped["Plan"] = relationship(back_populates="weeks", lazy="raise")
    sessions: Mapped[list["PlanSession"]] = relationship(
        back_populates="week",
        order_by="PlanSession.position",
        cascade="all, delete-orphan",
        lazy="raise",
    )


class PlanSession(Base):
    __tablename__ = "plan_sessions"
    __table_args__ = (
        CheckConstraint("position >= 1", name="position_positive"),
        CheckConstraint("max_minutes BETWEEN 20 AND 180", name="max_minutes_range"),
        CheckConstraint("weekday BETWEEN 1 AND 7", name="weekday_range"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    week_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("plan_weeks.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(SmallInteger)
    name: Mapped[str] = mapped_column(String(50))
    max_minutes: Mapped[int] = mapped_column(SmallInteger, default=60, server_default="60")
    weekday: Mapped[int | None] = mapped_column(SmallInteger)

    week: Mapped["PlanWeek"] = relationship(back_populates="sessions", lazy="raise")
    exercises: Mapped[list["PrescribedExercise"]] = relationship(
        back_populates="session",
        order_by="PrescribedExercise.slot",
        cascade="all, delete-orphan",
        lazy="raise",
    )


class PrescribedExercise(Base):
    __tablename__ = "prescribed_exercises"
    __table_args__ = (
        CheckConstraint("slot >= 1", name="slot_positive"),
        CheckConstraint("sets BETWEEN 1 AND 10", name="sets_range"),
        CheckConstraint(
            "rep_min IS NULL OR rep_max IS NULL OR rep_min <= rep_max", name="rep_range_order"
        ),
        Index(
            "ix_prescribed_exercises_session_id_active",
            "session_id",
            "slot",
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("plan_sessions.id", ondelete="CASCADE")
    )
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="RESTRICT"), index=True
    )
    slot: Mapped[int] = mapped_column(SmallInteger)
    sets: Mapped[int] = mapped_column(SmallInteger)
    rep_min: Mapped[int | None] = mapped_column(SmallInteger)
    rep_max: Mapped[int | None] = mapped_column(SmallInteger)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    session: Mapped["PlanSession"] = relationship(back_populates="exercises", lazy="raise")


class PlanMuscleTarget(Base):
    """Per-plan override of a muscle's priority; muscles without a row use priority 1.0."""

    __tablename__ = "plan_muscle_targets"
    __table_args__ = (CheckConstraint("priority >= 0", name="priority_non_negative"),)

    plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("plans.id", ondelete="CASCADE"), primary_key=True
    )
    muscle_id: Mapped[int] = mapped_column(
        ForeignKey("muscles.id", ondelete="CASCADE"), primary_key=True
    )
    priority: Mapped[float] = mapped_column(Float, default=1.0, server_default="1.0")

    plan: Mapped["Plan"] = relationship(back_populates="muscle_targets", lazy="raise")
