import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from config import settings
from pwdlib import PasswordHash


# ==============================
# EXCEPTIONS
# ==============================
class TokenError(Exception):
    """Invalid token: incorrect signature, token is outdated, it is of wrong type or no data is provided."""


# ==============================
# PASSWORD
# ==============================
_password_hash = PasswordHash.recommended()
_DUMMY_PASSWORD_HASH = _password_hash.hash(secrets.token_urlsafe(16))


def hash_password(plain_password: str) -> str:
    """Returns hashed password"""
    return _password_hash.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str | None) -> bool:
    """Checks password. If user is None - compares the password to dummy_hash to prevent timing attacks."""
    if hashed_password is None:
        _password_hash.verify(plain_password, _DUMMY_PASSWORD_HASH)
        return False
    return _password_hash.verify(plain_password, hashed_password)


def verify_and_update_password(plain_password: str, password_hash: str) -> tuple[bool, str | None]:
    """Verifies password and returns new hash if necessary
    @:returns (is_password_valid, new_hash|None)
    """
    return _password_hash.verify_and_update(plain_password, password_hash)


# ==============================
# ACCESS TOKEN
# ==============================


ACCESS_TOKEN_TYPE = "access"


def create_access_token(user_id: uuid.UUID, now: datetime | None = None) -> str:
    """Creates JWT.
    @:param now may override the issued_at for testing purposes."""
    issued_at = now or datetime.now(UTC)
    expires_at = issued_at + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {"sub": str(user_id), "type": ACCESS_TOKEN_TYPE, "iat": issued_at, "exp": expires_at}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> uuid.UUID:
    """Verifies JWT."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["exp", "iat", "sub"]},
        )

    except jwt.ExpiredSignatureError as e:
        raise TokenError("Token out of date") from e
    except jwt.InvalidTokenError as e:
        raise TokenError("Invalid token") from e

    if payload.get("type") != ACCESS_TOKEN_TYPE:
        raise TokenError("Invalid token type")

    try:
        return uuid.UUID(payload.get("sub"))
    except (ValueError, TypeError) as e:
        raise TokenError("Invalid user ID") from e


# ==============================
# REFRESH TOKEN
# ==============================


def generate_refresh_token() -> str:
    """Random 256bit token"""
    return secrets.token_urlsafe(32)


def hash_refresh_token(token: str) -> str:
    """Generates hashed token (SHA-256)."""
    return hashlib.sha256(token.encode()).hexdigest()


def refresh_token_expires_at(now: datetime | None = None) -> datetime:
    """Refreshes refresh token"""
    return now or datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
