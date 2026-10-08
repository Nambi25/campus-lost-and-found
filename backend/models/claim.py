from datetime import datetime

from pydantic import BaseModel, Field
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from models.user import utcnow

CLAIM_STATUSES = ("pending", "approved", "rejected")


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), index=True)
    claimant_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    claimant_name: Mapped[str] = mapped_column(String(100))
    details: Mapped[str] = mapped_column(Text)    # the private detail that proves ownership
    status: Mapped[str] = mapped_column(String(10), default="pending")
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    item = relationship("Item", back_populates="claims")
    claimant = relationship("User")


# ---------- request bodies ----------
class ClaimCreate(BaseModel):
    claimantName: str = Field(min_length=2, max_length=100)
    details: str = Field(min_length=12, max_length=1000)


class ClaimDecision(BaseModel):
    status: str   # approved | rejected
