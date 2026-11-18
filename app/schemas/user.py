"""Pydantic schemas for users (carried over from Module 10)."""
import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def username_chars(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", value):
            raise ValueError("username may contain only letters, digits, '_', '.', '-'")
        return value

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        if not re.search(r"[A-Z]", value):
            raise ValueError("password must contain an uppercase letter")
        if not re.search(r"[a-z]", value):
            raise ValueError("password must contain a lowercase letter")
        if not re.search(r"\d", value):
            raise ValueError("password must contain a digit")
        return value


class UserRead(BaseModel):
    """Public user data — the password hash is never exposed."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    created_at: datetime
