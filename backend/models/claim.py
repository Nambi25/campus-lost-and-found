import enum
from datetime import datetime

from pydantic import BaseModel, Field
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class ClaimStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    completed = "completed"   # item physically handed over


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), index=True)
    claimant_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    answer: Mapped[str] = mapped_column(Text, default="")        # answer to verification_question
    proof_details: Mapped[str] = mapped_column(Text, default="")  # serial no., marks, contents, etc.
    status: Mapped[ClaimStatus] = mapped_column(Enum(ClaimStatus), default=ClaimStatus.pending)
    handover_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    item = relationship("Item", back_populates="claims")
    claimant = relationship("User", foreign_keys=[claimant_id])


# ---------- Pydantic schemas ----------
class ClaimCreate(BaseModel):
    item_id: int
    answer: str = ""
    proof_details: str = Field(default="", max_length=2000)


class ClaimOut(BaseModel):
    id: int
    item_id: int
    claimant_id: int
    answer: str
    proof_details: str
    status: ClaimStatus
    handover_code: str | None = None
    created_at: datetime
    resolved_at: datetime | None

    claimant_name: str | None = None

    model_config = {"from_attributes": True}


class HandoverConfirm(BaseModel):
    handover_code: str

