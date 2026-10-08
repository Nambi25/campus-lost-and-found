import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    """A student.

    Two ways to be a user:
      * guest  – the frontend sends an `X-User-Id` header (a random id it keeps in localStorage).
                 This is what the current CampusFind frontend uses (it has no login screen).
      * account – register/login with email + password, then send `Authorization: Bearer <token>`.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[str] = mapped_column(String(64), unique=True, index=True,
                                           default=lambda: f"user-{uuid.uuid4().hex[:12]}")
    name: Mapped[str] = mapped_column(String(100), default="Student")
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    token: Mapped[str | None] = mapped_column(String(64), unique=True, index=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    items = relationship("Item", back_populates="poster")


# ---------- Pydantic schemas ----------
class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str          # public id — same value as posterId / claimantId in items
    name: str
    email: str | None


class TokenOut(BaseModel):
    token: str
    user: UserOut
