import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.domains.users.enums import UserRole


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    display_name: str | None
    role: UserRole
    created_at: datetime
