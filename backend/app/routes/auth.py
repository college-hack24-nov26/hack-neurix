"""
HomeCare+ — Authentication Routes (PostgreSQL Edition)
POST /auth/register
POST /auth/login
GET  /auth/profile
PUT  /auth/profile
PUT  /auth/password
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.middleware.auth import (
    create_access_token, get_current_user, hash_password, verify_password,
)
from app.models.models import GENDER_VALUES, User
from app.utils import iso

router = APIRouter()


def _blank_to_none(v):
    """The signup/settings forms send '' for untouched optional fields."""
    if isinstance(v, str) and not v.strip():
        return None
    return v


def _check_gender(v: Optional[str]) -> Optional[str]:
    v = _blank_to_none(v)
    if v is None:
        return None
    v = v.strip().lower()
    if v not in GENDER_VALUES:
        raise ValueError(f"Gender must be one of: {', '.join(GENDER_VALUES)}")
    return v


# ── Schemas ────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    firstName:   str
    lastName:    str
    email:       EmailStr
    phone:       Optional[str] = None
    dateOfBirth: Optional[date] = None
    gender:      Optional[str] = None
    password:    str

    @field_validator("phone", "dateOfBirth", mode="before")
    @classmethod
    def _blank(cls, v):
        return _blank_to_none(v)

    @field_validator("gender", mode="before")
    @classmethod
    def _gender(cls, v):
        return _check_gender(v)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


class ProfileUpdate(BaseModel):
    firstName:   Optional[str] = None
    lastName:    Optional[str] = None
    phone:       Optional[str] = None
    dateOfBirth: Optional[date] = None
    gender:      Optional[str] = None
    language:    Optional[str] = None

    @field_validator("phone", "dateOfBirth", "language", mode="before")
    @classmethod
    def _blank(cls, v):
        return _blank_to_none(v)

    @field_validator("gender", mode="before")
    @classmethod
    def _gender(cls, v):
        return _check_gender(v)


class PasswordChange(BaseModel):
    currentPassword: str
    newPassword:     str

    @field_validator("newPassword")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


def user_to_dict(user: User) -> dict:
    return {
        "id":          str(user.id),
        "firstName":   user.first_name,
        "lastName":    user.last_name,
        "email":       user.email,
        "phone":       user.phone,
        "dateOfBirth": iso(user.date_of_birth),
        "gender":      user.gender,
        "language":    user.language or "en",
        "createdAt":   iso(user.created_at),
    }


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    email = body.email.strip().lower()

    existing = await db.scalar(select(User.id).where(func.lower(User.email) == email))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists."
        )

    user = User(
        first_name=body.firstName.strip(),
        last_name=body.lastName.strip(),
        email=email,
        phone=body.phone,
        date_of_birth=body.dateOfBirth,
        gender=body.gender,
        password_hash=hash_password(body.password),
        language="en",
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:          # two simultaneous sign-ups with the same email
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists."
        )

    token = create_access_token({"sub": str(user.id)})
    return {"user": user_to_dict(user), "token": token}


@router.post("/login")
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    email = body.email.strip().lower()
    user = await db.scalar(
        select(User).where(func.lower(User.email) == email, User.is_active.is_(True))
    )
    if not user or not verify_password(body.password, user.password_hash or ""):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )
    token = create_access_token({"sub": str(user.id)})
    return {"user": user_to_dict(user), "token": token}


@router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    return {"user": user_to_dict(current_user)}


@router.put("/profile")
async def update_profile(
    body: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.firstName   is not None: current_user.first_name    = body.firstName
    if body.lastName    is not None: current_user.last_name     = body.lastName
    if body.phone       is not None: current_user.phone         = body.phone
    if body.dateOfBirth is not None: current_user.date_of_birth = body.dateOfBirth
    if body.gender      is not None: current_user.gender        = body.gender
    if body.language    is not None: current_user.language      = body.language

    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return {"user": user_to_dict(current_user)}


@router.put("/password")
async def change_password(
    body: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(body.currentPassword, current_user.password_hash or ""):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect."
        )

    current_user.password_hash = hash_password(body.newPassword)
    db.add(current_user)
    await db.commit()
    return {"message": "Password updated successfully."}
