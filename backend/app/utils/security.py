"""
Password hashing (bcrypt, used directly) and JWT creation/verification.

NOTE: We call the `bcrypt` library directly rather than going through
passlib's CryptContext. passlib 1.7.4 (the latest release) cannot read
version metadata from bcrypt>=4.1.0 and raises errors — a known,
long-standing incompatibility between the two unmaintained/fast-moving
packages. Calling bcrypt directly sidesteps it entirely and is one
less layer of dependency.
"""
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.config import settings

# bcrypt has a hard 72-byte input limit; longer passwords are truncated
# to the first 72 bytes before hashing (matches bcrypt's own behavior).
_BCRYPT_MAX_BYTES = 72


def _prepare(password: str) -> bytes:
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(plain_password: str) -> str:
    hashed = bcrypt.hashpw(_prepare(plain_password), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(_prepare(plain_password), password_hash.encode("utf-8"))
    except ValueError:
        # Malformed/legacy hash — treat as a failed verification, not a crash.
        return False


def create_access_token(subject: str, extra_claims: dict[str, Any] | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {"sub": subject, "exp": expire}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Raises jwt.PyJWTError (or subclasses) if invalid/expired — caught by callers."""
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
