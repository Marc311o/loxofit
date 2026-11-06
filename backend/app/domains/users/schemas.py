import uuid
from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domains.users.enums import ExperienceLevel, UserRole

Weekday = Annotated[int, Field(ge=1, le=7)]


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    display_name: str | None
    role: UserRole
    created_at: datetime


class ProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    experience: ExperienceLevel
    days_per_week: int
    max_session_minutes: int
    preferred_weekdays: list[int] | None
    weight_kg: float | None
    updated_at: datetime


class ProfileWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    experience: ExperienceLevel
    days_per_week: int = Field(ge=1, le=7)
    max_session_minutes: int = Field(default=60, ge=20, le=180)
    preferred_weekdays: list[Weekday] | None = Field(default=None, max_length=7)
    weight_kg: float | None = Field(default=None, ge=30, le=300)

    @field_validator("preferred_weekdays")
    @classmethod
    def _unique_sorted(cls, days: list[int] | None) -> list[int] | None:
        if days is None:
            return None
        if len(days) != len(set(days)):
            raise ValueError("weekdays must be unique")
        return sorted(days)


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str | None = Field(default=None, min_length=1, max_length=100)


class EquipmentIdsWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    equipment_ids: list[int] = Field(max_length=100)

    @model_validator(mode="after")
    def _unique(self) -> Self:
        if len(self.equipment_ids) != len(set(self.equipment_ids)):
            raise ValueError("equipment ids must be unique")
        return self
