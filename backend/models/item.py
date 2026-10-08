import enum
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class ItemType(str, enum.Enum):
    lost = "lost"
    found = "found"


class ItemStatus(str, enum.Enum):
    open = "open"          # visible, waiting for a match/claim
    claimed = "claimed"    # a claim was approved, handover pending
    returned = "returned"  # handed over, closed


CATEGORIES = [
    "id_card", "electronics", "earbuds", "calculator", "bag",
    "bottle", "keys", "wallet", "books", "clothing", "other",
]


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[ItemType] = mapped_column(Enum(ItemType), index=True)
    title: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(50), index=True, default="other")
    location: Mapped[str] = mapped_column(String(150), index=True)
    event_time: Mapped[datetime] = mapped_column(DateTime)          # when it was lost/found
    image_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    image_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)   # perceptual hash
    color_sig: Mapped[str | None] = mapped_column(String(255), nullable=True)   # colour histogram
    # Finder sets a private question only the real owner can answer (e.g. "What's the lock-screen wallpaper?")
    verification_question: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[ItemStatus] = mapped_column(Enum(ItemStatus), default=ItemStatus.open, index=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    reporter = relationship("User", back_populates="items")
    claims = relationship("Claim", back_populates="item", cascade="all, delete-orphan")


# ---------- Pydantic schemas ----------
class ItemOut(BaseModel):
    id: int
    type: ItemType
    title: str
    description: str
    category: str
    location: str
    event_time: datetime
    image_url: str | None = None
    verification_question: str | None
    status: ItemStatus
    reporter_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class MatchOut(BaseModel):
    item: ItemOut
    score: float           # 0..1 combined
    image_score: float | None
    text_score: float
