from app.core.errors import ConflictError


class EmailAlreadyTakenError(ConflictError):
    code = "EMAIL_TAKEN"
    detail = "Account with this email address already exists"
