"""Items: report lost/found, browse/search, AI matches, search-by-photo."""
import os
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from database import get_db
from models.item import CATEGORIES, Item, ItemOut, ItemStatus, ItemType, MatchOut
from models.claim import Claim
from models.user import User
from routes.users import get_current_user
from services import item_service

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/categories", response_model=list[str])
def list_categories():
    return CATEGORIES


@router.post("", response_model=ItemOut, status_code=201)
async def create_item(
    type: ItemType = Form(...),
    title: str = Form(..., min_length=2, max_length=150),
    location: str = Form(...),
    description: str = Form(""),
    category: str = Form("other"),
    event_time: datetime | None = Form(None),     # ISO string, e.g. 2026-10-08T10:30
    verification_question: str | None = Form(None),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Multipart form (because of the image). Frontend: use FormData."""
    if category not in CATEGORIES:
        raise HTTPException(400, f"category must be one of {CATEGORIES}")

    item = Item(
        type=type,
        title=title.strip(),
        description=description.strip(),
        category=category,
        location=location.strip(),
        event_time=event_time or datetime.utcnow(),
        verification_question=verification_question if type == ItemType.found else None,
        reporter_id=user.id,
    )
    if image and image.filename:
        item.image_path, item.image_hash, item.color_sig = await item_service.save_image(image)

    db.add(item)
    db.commit()
    db.refresh(item)
    return item_service.to_out(item)


@router.get("", response_model=list[ItemOut])
def list_items(
    q: str | None = None,
    type: ItemType | None = None,
    category: str | None = None,
    location: str | None = None,
    status: ItemStatus | None = ItemStatus.open,
    limit: int = Query(20, le=100),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    items = item_service.search_items(db, q, type, category, location, status, limit, offset)
    return [item_service.to_out(i) for i in items]


@router.get("/mine", response_model=list[ItemOut])
def my_items(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    items = db.query(Item).filter(Item.reporter_id == user.id).order_by(Item.created_at.desc()).all()
    return [item_service.to_out(i) for i in items]


@router.post("/search-by-image", response_model=list[MatchOut])
async def search_by_image(
    image: UploadFile = File(...),
    type: ItemType = Form(ItemType.found),   # usually "I lost this, show me FOUND items"
    category: str = Form("other"),
    description: str = Form(""),
    db: Session = Depends(get_db),
):
    """Upload a photo of your item (or a similar one) -> ranked candidates. Nothing is saved."""
    path, phash, color = await item_service.save_image(image)
    os.remove(path)
    probe = Item(
        type=ItemType.lost if type == ItemType.found else ItemType.found,
        title="", description=description, category=category,
        image_hash=phash, color_sig=color,
    )
    return item_service.find_matches(db, probe, limit=10, min_score=0.2)


@router.get("/stats", tags=["items"])
def board_stats(db: Session = Depends(get_db)):
    """Public board counters used by the frontend."""
    active = db.query(Item).filter(Item.status.in_([ItemStatus.open, ItemStatus.claimed])).count()
    found = db.query(Item).filter(Item.type == ItemType.found, Item.status == ItemStatus.open).count()
    lost = db.query(Item).filter(Item.type == ItemType.lost, Item.status == ItemStatus.open).count()
    claims = db.query(Claim).filter(Claim.status == "pending").count()
    return {"active": active, "found": found, "lost": lost, "claims": claims}


@router.get("/{item_id}", response_model=ItemOut)
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    return item_service.to_out(item)


@router.get("/{item_id}/matches", response_model=list[MatchOut])
def get_matches(item_id: int, limit: int = 5, db: Session = Depends(get_db)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    return item_service.find_matches(db, item, limit=limit)


@router.patch("/{item_id}/status", response_model=ItemOut)
def update_status(
    item_id: int,
    status: ItemStatus = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Reporter can close their own post (e.g. 'found it myself')."""
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    if item.reporter_id != user.id:
        raise HTTPException(403, "Only the reporter can change this")
    item.status = status
    db.commit()
    db.refresh(item)
    return item_service.to_out(item)


@router.delete("/{item_id}", status_code=204)
def delete_item(item_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    if item.reporter_id != user.id:
        raise HTTPException(403, "Only the reporter can delete this")
    if item.image_path and os.path.exists(item.image_path):
        os.remove(item.image_path)
    db.delete(item)
    db.commit()
