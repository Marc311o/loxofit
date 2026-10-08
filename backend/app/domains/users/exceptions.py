from app.core.errors import ConflictError


class EmailTakenError(ConflictError):
    code = "EMAIL_TAKEN"
    detail = "Account with this email address already exists"
