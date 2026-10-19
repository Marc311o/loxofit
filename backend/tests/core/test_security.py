"""Unit tests for app.core.security: passwords, JWT access tokens, refresh tokens."""

import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core import security
from app.core.config import settings

PASSWORD = "secret-password-123"


def _payload(**overrides: object) -> dict[str, object]:
    """Valid access-token payload; override fields to build broken tokens."""
    now = datetime.now(UTC)
    return {
        "sub": str(uuid.uuid4()),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=5),
        **overrides,
    }


# ---------------------------------------------------------------------------
# Passwords
# ---------------------------------------------------------------------------


def test_hash_is_not_plain_and_uses_argon2():
    hashed = security.hash_password(PASSWORD)
    assert hashed != PASSWORD
    assert hashed.startswith("$argon2")


def test_verify_password_correct_and_wrong():
    hashed = security.hash_password(PASSWORD)
    assert security.verify_password(PASSWORD, hashed) is True
    assert security.verify_password("wrong-password", hashed) is False


def test_same_password_gives_different_hashes():
    # A new random salt for every hash.
    assert security.hash_password(PASSWORD) != security.hash_password(PASSWORD)


def test_verify_password_without_user_returns_false():
    # No user -> no hash; the dummy hash is still verified (timing-attack protection).
    assert security.verify_password("anything", None) is False


# ---------------------------------------------------------------------------
# Access token
# ---------------------------------------------------------------------------


def test_access_token_roundtrip():
    user_id = uuid.uuid4()
    token = security.create_access_token(user_id)
    assert security.decode_access_token(token) == user_id


def test_tampered_token_is_rejected():
    token = security.create_access_token(uuid.uuid4())
    tampered = token[:-2] + ("A" if token[-2] != "A" else "B") + token[-1]
    with pytest.raises(security.TokenError):
        security.decode_access_token(tampered)


def test_token_signed_with_other_key_is_rejected():
    foreign = jwt.encode(_payload(), "another-secret-key-" * 3, algorithm="HS256")
    with pytest.raises(security.TokenError):
        security.decode_access_token(foreign)


def test_expired_token_is_rejected():
    long_ago = datetime.now(UTC) - timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES + 5)
    token = security.create_access_token(uuid.uuid4(), now=long_ago)
    with pytest.raises(security.TokenError) as exc_info:
        security.decode_access_token(token)
    assert isinstance(exc_info.value.__cause__, jwt.ExpiredSignatureError)


def test_wrong_token_type_is_rejected():
    # Correctly signed and not expired - the only problem is the type.
    token = jwt.encode(
        _payload(type="reset_password"), settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    with pytest.raises(security.TokenError):
        security.decode_access_token(token)


def test_alg_none_is_rejected():
    unsigned = jwt.encode(_payload(), None, algorithm="none")
    with pytest.raises(security.TokenError):
        security.decode_access_token(unsigned)


# ---------------------------------------------------------------------------
# Refresh token
# ---------------------------------------------------------------------------


def test_refresh_tokens_are_unique():
    assert security.generate_refresh_token() != security.generate_refresh_token()


def test_refresh_token_hash_is_deterministic_sha256():
    token = security.generate_refresh_token()
    hashed = security.hash_refresh_token(token)
    assert len(hashed) == 64  # SHA-256 hex digest
    assert hashed == security.hash_refresh_token(token)
    assert hashed != token
