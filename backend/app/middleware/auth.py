"""
HomeCare+ — JWT Authentication Middleware (PostgreSQL Edition)
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from jose import JWTError, jwt
from passlib.context import CryptContext

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.config.database import get_db
from app.models.models import User


# ─────────────────────────────────────────────────────────────
# Password Hashing Configuration
# Using Argon2 (modern secure algorithm, no 72-byte limit)
# ─────────────────────────────────────────────────────────────
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)


# ─────────────────────────────────────────────────────────────
# Bearer Authentication Scheme
# ─────────────────────────────────────────────────────────────
bearer_scheme = HTTPBearer()


# ─────────────────────────────────────────────────────────────
# Password Hashing
# ─────────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    """Securely hash a password."""

    if not password:
        raise ValueError("Password cannot be empty")

    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters")

    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against stored hash."""

    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────
# JWT Token Creation
# ─────────────────────────────────────────────────────────────
def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Generate a JWT access token. `sub` should be the user's id (UUID string)."""

    to_encode = data.copy()

    # JWT subject must be string
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])

    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


# ─────────────────────────────────────────────────────────────
# JWT Token Decode
# ─────────────────────────────────────────────────────────────
def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Safely decode JWT token."""

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        return payload

    except JWTError:
        return None


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────
def parse_uuid(value) -> Optional[uuid.UUID]:
    """Return a UUID or None (never raises) — used for ids coming from URLs/tokens."""
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except (ValueError, AttributeError, TypeError):
        return None


async def _load_active_user(db: AsyncSession, user_id: str) -> Optional[User]:
    uid = parse_uuid(user_id)
    if uid is None:
        return None
    result = await db.execute(select(User).where(User.id == uid, User.is_active.is_(True)))
    return result.scalar_one_or_none()


# ─────────────────────────────────────────────────────────────
# Get Current Authenticated User
# ─────────────────────────────────────────────────────────────
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Return the authenticated `User` row, or raise 401."""

    payload = decode_token(credentials.credentials)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None or parse_uuid(user_id) is None:
        # also rejects old MongoDB ObjectId tokens issued before the migration
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    user = await _load_active_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    return user


# ─────────────────────────────────────────────────────────────
# Optional Authentication (for public endpoints)
# ─────────────────────────────────────────────────────────────
async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Returns the authenticated user if a valid token is present, otherwise None."""

    if not credentials:
        return None

    payload = decode_token(credentials.credentials)
    if not payload or not payload.get("sub"):
        return None

    return await _load_active_user(db, payload["sub"])
