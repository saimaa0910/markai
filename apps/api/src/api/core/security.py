import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Union
import bcrypt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from jose import jwt
from api.core.config import settings

ALGORITHM = "HS256"
_password_hasher = PasswordHasher()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its hashed value.
    """
    if hashed_password.startswith("$argon2"):
        try:
            return _password_hasher.verify(hashed_password, plain_password)
        except (InvalidHashError, VerificationError, VerifyMismatchError):
            return False

    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """
    Generate an Argon2id hash of the password.
    """
    return _password_hasher.hash(password)


def create_access_token(
    subject: Union[str, Any] = None,
    expires_delta: Union[timedelta, None] = None,
    token_id: Union[str, uuid.UUID, None] = None,
    data: Union[dict, None] = None,
) -> str:
    """
    Generate a JWT access token for the subject.
    """
    sub = subject
    if data and "sub" in data:
        sub = data["sub"]

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {
        "exp": expire,
        "sub": str(sub),
        "type": "access",
        "jti": str(token_id or uuid.uuid4()),
    }
    # Carry extra claims (e.g. session_id) from data into the token payload.
    if data:
        for key, value in data.items():
            if key == "sub":
                continue
            to_encode[key] = value
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return str(encoded_jwt)


def create_refresh_token(
    subject: Union[str, Any], expires_delta: Union[timedelta, None] = None
) -> str:
    """
    Generate a JWT refresh token for the subject.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",
        "jti": str(uuid.uuid4()),
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return str(encoded_jwt)
