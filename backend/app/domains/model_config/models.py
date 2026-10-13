from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    false,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.domains.catalog.enums import MuscleRole
from app.domains.model_config.enums import VolumeMode


class ModelConfig(Base):
    __tablename__ = "model_configs"
    __table_args__ = (
        Index(
            "uq_model_configs_single_default",
            "is_default",
            unique=True,
            postgresql_where=text("is_default"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    volume_mode: Mapped[VolumeMode] = mapped_column(
        Enum(
            VolumeMode,
            name="volume_mode",
            values_callable=lambda e: [member.value for member in e],
        ),
        default=VolumeMode.GLOBAL,
        server_default=VolumeMode.GLOBAL,
    )
    global_mev: Mapped[float | None] = mapped_column(Float)
    global_mav_upper: Mapped[float | None] = mapped_column(Float)
    global_mrv: Mapped[float | None] = mapped_column(Float)
    penalty_lambda: Mapped[float] = mapped_column(Float, default=0.05, server_default="0.05")
    curve_k: Mapped[float] = mapped_column(Float, default=3, server_default="3")
    rest_compound_s: Mapped[int] = mapped_column(Integer, default=150, server_default="150")
    rest_isolation_s: Mapped[int] = mapped_column(Integer, default=90, server_default="90")
    transitions_s: Mapped[int] = mapped_column(Integer, default=90, server_default="90")
    warmup_s: Mapped[int] = mapped_column(Integer, default=300, server_default="300")
    explosive_phase_s: Mapped[float] = mapped_column(Float, default=1.0, server_default="1.0")
    time_penalty: Mapped[float] = mapped_column(Float, default=0.1, server_default="0.1")
    weekly_volume_increase: Mapped[float] = mapped_column(
        Float, default=0.15, server_default="0.15"
    )
    max_sets_per_exercise: Mapped[int] = mapped_column(Integer, default=5, server_default="5")
    rir_start: Mapped[int] = mapped_column(Integer, default=3, server_default="3")
    rir_end: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    deload_volume_factor: Mapped[float] = mapped_column(Float, default=0.5, server_default="0.5")
    deload_rir: Mapped[int] = mapped_column(Integer, default=4, server_default="4")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    role_weights: Mapped[list["ConfigRoleWeight"]] = relationship(
        back_populates="config", cascade="all, delete-orphan", lazy="raise"
    )


class ConfigRoleWeight(Base):
    __tablename__ = "config_role_weights"
    __table_args__ = (CheckConstraint("weight >= 0", name="weight_non_negative"),)

    config_id: Mapped[int] = mapped_column(
        ForeignKey("model_configs.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[MuscleRole] = mapped_column(
        Enum(
            MuscleRole,
            name="muscle_role",
            values_callable=lambda e: [member.value for member in e],
        ),
        primary_key=True,
    )
    weight: Mapped[float] = mapped_column(Float)
    config: Mapped[ModelConfig] = relationship(back_populates="role_weights", lazy="raise")
