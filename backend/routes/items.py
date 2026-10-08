"""Items — every response is in the exact shape the CampusFind React app reads."""
import os
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from database import get_db
from models.claim import Claim
from models.item import (CATEGORIES, KINDS, STATUSES, Item, ItemOut, MatchesOut, MatchOut,
                         MyItemsOut, StatsOut, StatusUpdate)
from models.user import User, utcnow
from routes.users import get_current_user, get_optional_user
from services import item_service as svc

router = APIRouter(prefix="/items", tags=["items"])


def _get_item(db: Session, item_id: int) -> Item:
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(404, "This report is no longer available.")
    return item


@router.get("/categories", response_model=list[str])
def list_categories():
    return CATEGORIES


@router.get("/stats", response_model=StatsOut)
def get_stats(db: Session = Depends(get_db)):
    return svc.board_stats(db)


@router.get("/mine", response_model=MyItemsOut)
def my_items(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Reports I posted + claims I submitted (for the My items page)."""
    reports = db.query(Item).filter(Item.poster_id == user.id).order_by(Item.reported_at.desc()).all()
    claims = []
    for c in db.query(Claim).filter(Claim.claimant_id == user.id).order_by(Claim.submitted_at.desc()):
        claims.append({**svc.serialize_claim(c, user), "itemId": c.item.id, "itemTitle": c.item.title,
                       "itemImageUrl": svc.image_url(c.item), "itemKind": c.item.kind,
                       "itemStatus": c.item.status})
    return {"reports": [svc.serialize_item(i, user) for i in reports], "claims": claims}


@router.get("", response_model=list[ItemOut])
def list_items(
    query: str = "", kind: str = "all", category: str = "all", location: str = "all",
    recency: str = "all", claimState: str = "all",
    db: Session = Depends(get_db), viewer: User | None = Depends(get_optional_user),
):
    items = svc.search_items(db, query, kind, category, location, recency, claimState)
    return [svc.serialize_item(i, viewer) for i in items]


@router.post("", response_model=ItemOut, status_code=201)
async def create_item(
    kind: str = Form(...),
    title: str = Form(..., min_length=3, max_length=120),
    category: str = Form(...),
    description: str = Form(..., min_length=12, max_length=600),
    location: str = Form(..., min_length=1, max_length=120),
    timestamp: datetime | None = Form(None),   # from <input type="datetime-local">
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Multipart form (FormData) because of the photo. Photo is required for found items."""
    if kind not in KINDS:
        raise HTTPException(400, "kind must be 'lost' or 'found'")
    if category not in CATEGORIES:
        raise HTTPException(400, f"category must be one of {CATEGORIES}")
    has_image = image is not None and bool(image.filename)
    if kind == "found" and not has_image:
        raise HTTPException(400, "Add one clear photo so another student can recognize it.")

    item = Item(kind=kind, title=title.strip(), category=category, description=description.strip(),
                location=location.strip(), event_at=timestamp or utcnow(), poster_id=user.id)
    if has_image:
        item.image_path, item.image_hash, item.color_sig = await svc.save_image(image)
        item.image_name = image.filename or ""
    db.add(item)
    db.commit()
    db.refresh(item)
    return svc.serialize_item(item, user)


@router.post("/search-by-image", response_model=list[MatchOut])
async def search_by_image(
    image: UploadFile = File(...),
    kind: str = Form("found"),          # which reports to search: usually FOUND ones
    category: str = Form("Other"),
    description: str = Form(""),
    db: Session = Depends(get_db), viewer: User | None = Depends(get_optional_user),
):
    """Upload a photo -> ranked lookalike reports. Nothing is saved."""
    path, phash, color = await svc.save_image(image)
    os.remove(path)
    probe = Item(id=-1, kind="lost" if kind == "found" else "found", title="", description=description,
                 category=category, location="", event_at=utcnow(), image_hash=phash, color_sig=color)
    return svc.find_matches(db, probe, viewer, limit=10, min_score=0.2)["matches"]


@router.get("/{item_id}", response_model=ItemOut)
def get_item(item_id: int, db: Session = Depends(get_db), viewer: User | None = Depends(get_optional_user)):
    return svc.serialize_item(_get_item(db, item_id), viewer)


@router.get("/{item_id}/matches", response_model=MatchesOut)
def get_matches(item_id: int, db: Session = Depends(get_db), viewer: User | None = Depends(get_optional_user)):
    return svc.find_matches(db, _get_item(db, item_id), viewer)


@router.patch("/{item_id}/status", response_model=ItemOut)
def update_status(item_id: int, body: StatusUpdate, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    if body.status not in STATUSES:
        raise HTTPException(400, "Unsupported report status.")
    item = _get_item(db, item_id)
    if item.poster_id != user.id:
        raise HTTPException(403, "Only the report owner can change this status.")
    item.status = body.status
    item.updated_at = utcnow()
    db.commit()
    db.refresh(item)
    return svc.serialize_item(item, user)


@router.delete("/{item_id}", status_code=204)
def delete_item(item_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = _get_item(db, item_id)
    if item.poster_id != user.id:
        raise HTTPException(403, "Only the report owner can delete this.")
    if item.image_path and os.path.exists(item.image_path):
        os.remove(item.image_path)
    db.delete(item)
    db.commit()
