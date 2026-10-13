import enum


class UserRole(enum.StrEnum):
    USER = "user"
    ADMIN = "admin"


class ExperienceLevel(enum.StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERIENCED = "experienced"
