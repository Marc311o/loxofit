from app.core.errors import AuthenticationError, PermissionDeniedError


class InvalidCredentialsError(AuthenticationError):
    code = "INVALID_CREDENTIALS"
    detail = "Invalid email or password"


class InactiveAccountError(PermissionDeniedError):
    code = "ACCOUNT_INACTIVE"
    detail = "The account is inactive"


class InvalidRefreshTokenError(AuthenticationError):
    code = "INVALID_REFRESH_TOKEN"
    detail = "Session expired, proceed to log in again"
