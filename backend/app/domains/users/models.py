import uuid
from datetime import datetime

from sqlalchemy import UUID, Boolean, DateTime, Enum, String, func, true
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.domains.users.enums import UserRole


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
