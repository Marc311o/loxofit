import uuid
from datetime import datetime

from sqlalchemy import (
    ARRAY,
    UUID,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    SmallInteger,
    String,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.domains.users.enums import ExperienceLevel, UserRole

# TODO (optional): Compare user strength against normative data
#  (relative squat/bench/deadlift strength by sex, age and body mass;
#  JSAMS 2024, 809,986 entries, doi:10.1016/j.jsams.2024.07.005).
#  Requires adding sex and birth_year to the profile (weight_kg already exists)
#  and 1RM estimation from S5. No height or BMI.


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(250), unique=True)
    password_hash: Mapped[str] = mapped_column(String)
    display_name: Mapped[str | None] = mapped_column(String(100))
    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            name="user_role",
            values_callable=lambda e: [member.value for member in e],
        ),
        default=UserRole.USER,
        server_default=UserRole.USER.value,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    profile: Mapped["UserProfile | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="raise"
    )


class UserProfile(Base):
    __tablename__ = "user_profiles"
    __table_args__ = (
        CheckConstraint("days_per_week BETWEEN 1 AND 7", name="days_per_week_range"),
        CheckConstraint(
            "preferred_weekdays <@ ARRAY[1,2,3,4,5,6,7]::smallint[]",
            name="preferred_weekdays_valid",
        ),
        CheckConstraint("max_session_minutes BETWEEN 20 AND 180", name="max_session_minutes_range"),
        CheckConstraint("weight_kg BETWEEN 30 AND 300", name="weight_kg_range"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    experience: Mapped[ExperienceLevel] = mapped_column(
        Enum(
            ExperienceLevel,
            name="experience_level",
            values_callable=lambda e: [member.value for member in e],
        )
    )
    days_per_week: Mapped[int] = mapped_column(SmallInteger)
    max_session_minutes: Mapped[int] = mapped_column(SmallInteger, default=60, server_default="60")
    preferred_weekdays: Mapped[list[int] | None] = mapped_column(ARRAY(SmallInteger))
    weight_kg: Mapped[float | None] = mapped_column(Float)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="profile", lazy="raise")
