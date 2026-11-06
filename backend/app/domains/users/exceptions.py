from app.core.errors import AppError, ConflictError, NotFoundError


class EmailAlreadyTakenError(ConflictError):
    code = "EMAIL_TAKEN"
    detail = "Account with this email address already exists"


class ProfileNotFoundError(NotFoundError):
    code = "PROFILE_NOT_FOUND"
    detail = "User profile not set up yet"


class InvalidEquipmentError(AppError):
    status_code = 422
    code = "INVALID_EQUIPMENT"
    detail = "Unknown equipment"
