from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Enum,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    false,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.domains.catalog.enums import EquipmentCategory, MovementPattern, MuscleGroup, MuscleRole


class Muscle(Base):
    __tablename__ = "muscles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(10), unique=True)
    name_en: Mapped[str] = mapped_column(String(100))
    name_pl: Mapped[str] = mapped_column(String(100))
    muscle_group: Mapped[MuscleGroup] = mapped_column(
        Enum(
            MuscleGroup,
            name="muscle_group",
            values_callable=lambda e: [member.value for member in e],
        )
    )
    description_en: Mapped[str | None] = mapped_column(Text)
    description_pl: Mapped[str | None] = mapped_column(Text)
    is_volume_target: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())

    exercise_roles: Mapped[list["ExerciseMuscleRole"]] = relationship(
        back_populates="muscle", lazy="raise"
    )


class Equipment(Base):
    __tablename__ = "equipment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name_en: Mapped[str] = mapped_column(String(100), unique=True)
    name_pl: Mapped[str] = mapped_column(String(100), unique=True)
    description_en: Mapped[str | None] = mapped_column(Text)
    description_pl: Mapped[str | None] = mapped_column(Text)
    category: Mapped[EquipmentCategory] = mapped_column(
        Enum(
            EquipmentCategory,
            name="equipment_category",
            values_callable=lambda e: [member.value for member in e],
        )
    )


class Exercise(Base):
    __tablename__ = "exercises"
    __table_args__ = (
        CheckConstraint("fatigue_cost BETWEEN 1 AND 5", name="fatigue_cost_range"),
        CheckConstraint("complexity BETWEEN 1 AND 5", name="complexity_range"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name_en: Mapped[str] = mapped_column(String(150), unique=True)
    name_pl: Mapped[str] = mapped_column(String(150), unique=True)
    main_group: Mapped[MuscleGroup] = mapped_column(
        Enum(
            MuscleGroup,
            name="muscle_group",
            values_callable=lambda e: [member.value for member in e],
        ),
        index=True,
    )
    movement_pattern: Mapped[MovementPattern] = mapped_column(
        Enum(
            MovementPattern,
            name="movement_pattern",
            values_callable=lambda e: [member.value for member in e],
        ),
        index=True,
    )
    is_compound: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    is_unilateral: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    fatigue_cost: Mapped[int] = mapped_column(SmallInteger)
    complexity: Mapped[int] = mapped_column(SmallInteger)
    default_tempo: Mapped[str | None] = mapped_column(String(4))
    instructions_pl: Mapped[str | None] = mapped_column(Text)
    instructions_en: Mapped[str | None] = mapped_column(Text)

    equipment: Mapped[list["Equipment"]] = relationship(
        secondary="exercise_equipment", order_by="Equipment.name_en", lazy="raise"
    )
    muscle_roles: Mapped[list["ExerciseMuscleRole"]] = relationship(
        back_populates="exercise",
        order_by="ExerciseMuscleRole.role",
        cascade="all, delete-orphan",
        lazy="raise",
    )
    substitutes: Mapped[list["ExerciseSubstitute"]] = relationship(
        foreign_keys="ExerciseSubstitute.exercise_id",
        back_populates="exercise",
        cascade="all, delete-orphan",
        lazy="raise",
    )


class ExerciseEquipment(Base):
    __tablename__ = "exercise_equipment"

    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"), primary_key=True
    )
    equipment_id: Mapped[int] = mapped_column(
        ForeignKey("equipment.id", ondelete="CASCADE"), primary_key=True, index=True
    )


class ExerciseMuscleRole(Base):
    __tablename__ = "exercise_muscle_roles"

    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"), primary_key=True
    )
    muscle_id: Mapped[int] = mapped_column(
        ForeignKey("muscles.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    role: Mapped[MuscleRole] = mapped_column(
        Enum(
            MuscleRole,
            name="muscle_role",
            values_callable=lambda e: [member.value for member in e],
        )
    )
    exercise: Mapped["Exercise"] = relationship(back_populates="muscle_roles", lazy="raise")
    muscle: Mapped["Muscle"] = relationship(back_populates="exercise_roles", lazy="raise")


class ExerciseSubstitute(Base):
    __tablename__ = "exercise_substitutes"
    __table_args__ = (CheckConstraint("exercise_id != substitute_exercise_id", name="not_self"),)

    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"), primary_key=True
    )
    substitute_exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    priority_score: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    exercise: Mapped["Exercise"] = relationship(
        foreign_keys=[exercise_id], back_populates="substitutes", lazy="raise"
    )
    substitute: Mapped["Exercise"] = relationship(
        foreign_keys=[substitute_exercise_id], lazy="raise"
    )
