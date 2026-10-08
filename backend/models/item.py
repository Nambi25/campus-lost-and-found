from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from models.user import utcnow

# Must match the dropdowns in frontend ItemForm.jsx / SearchBar.jsx
CATEGORIES = ["Electronics", "School supplies", "Bags & accessories", "Clothing", "Keys & cards", "Other"]
KINDS = ("lost", "found")
STATUSES = ("active", "resolved")


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(10), index=True)              # lost | found
    title: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(50), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    location: Mapped[str] = mapped_column(String(120), index=True)
    event_at: Mapped[datetime] = mapped_column(DateTime)                    # when lost / found
    reported_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(10), default="active", index=True)  # active | resolved
    image_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    image_name: Mapped[str] = mapped_column(String(255), default="")
    image_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)   # perceptual hash
    color_sig: Mapped[str | None] = mapped_column(Text, nullable=True)          # colour histogram
    poster_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    poster = relationship("User", back_populates="items")
    claims = relationship("Claim", back_populates="item", cascade="all, delete-orphan",
                          order_by="desc(Claim.submitted_at)")


# ---------- response shapes (camelCase = exactly what the React app reads) ----------
class ClaimOut(BaseModel):
    id: int
    claimantId: str
    claimantName: str
    details: str
    submittedAt: datetime
    reviewedAt: datetime | None = None
    status: str


class ItemOut(BaseModel):
    id: int
    kind: str
    title: str
    category: str
    description: str
    location: str
    eventAt: datetime
    reportedAt: datetime
    updatedAt: datetime | None = None
    status: str
    imageUrl: str | None
    imageName: str
    posterId: str
    posterName: str
    claims: list[ClaimOut]


class StatusUpdate(BaseModel):
    status: str


class MatchOut(BaseModel):
    item: ItemOut
    score: float
    reason: str
    imageScore: float | None = None


class MatchesOut(BaseModel):
    mode: str          # "image+text" when photos were compared, otherwise "text"
    matches: list[MatchOut]


class StatsOut(BaseModel):
    active: int
    found: int
    lost: int
    claims: int


class MyClaimOut(ClaimOut):
    itemId: int
    itemTitle: str
    itemImageUrl: str | None
    itemKind: str
    itemStatus: str


class MyItemsOut(BaseModel):
    reports: list[ItemOut]
    claims: list[MyClaimOut]
