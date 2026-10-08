"""Business logic: image storage, serialisation to the frontend's shape, search, matching, stats.

Image similarity runs on any laptop (no GPU / model download):
  * perceptual hash (pHash)  -> same object photographed again
  * colour histogram         -> similar-looking object
It is combined with the same text signals the frontend demo used
(category, campus spot, shared words, recency) into one 0..1 score.
Swap `image_similarity()` for CLIP embeddings later if there's time.
"""
import json
import os
import re
import uuid
from datetime import timedelta

import imagehash
from fastapi import HTTPException, UploadFile
from PIL import Image
from sqlalchemy.orm import Session

from models.claim import Claim
from models.item import Item
from models.user import User, utcnow

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
ALLOWED_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024

os.makedirs(UPLOAD_DIR, exist_ok=True)


# ---------- images ----------
async def save_image(file: UploadFile) -> tuple[str, str, str]:
    """Saves an upload. Returns (path, phash, colour signature)."""
    ext = ALLOWED_TYPES.get(file.content_type or "")
    if not ext:
        raise HTTPException(400, "Choose a JPG, PNG, WebP or GIF image.")
    data = await file.read()
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(400, "Image too large (max 5 MB).")
    path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}{ext}")
    with open(path, "wb") as f:
        f.write(data)
    try:
        img = Image.open(path).convert("RGB")
    except Exception:
        os.remove(path)
        raise HTTPException(400, "Could not read that image. Please choose another file.")
    return path, str(imagehash.phash(img)), json.dumps(color_signature(img))


def color_signature(img: Image.Image, bins: int = 4) -> list[float]:
    small = img.resize((64, 64))
    counts = [0] * (bins ** 3)
    step = 256 // bins
    raw = small.tobytes()
    for i in range(0, len(raw), 3):
        r, g, b = raw[i], raw[i + 1], raw[i + 2]
        counts[(r // step) * bins * bins + (g // step) * bins + (b // step)] += 1
    total = sum(counts)
    return [c / total for c in counts]


def image_similarity(a: Item, b: Item) -> float | None:
    if not (a.image_hash and b.image_hash):
        return None
    dist = imagehash.hex_to_hash(a.image_hash) - imagehash.hex_to_hash(b.image_hash)
    hash_sim = max(0.0, 1 - dist / 32)
    color_sim = 0.0
    if a.color_sig and b.color_sig:
        color_sim = sum(min(x, y) for x, y in zip(json.loads(a.color_sig), json.loads(b.color_sig)))
    return round(0.6 * hash_sim + 0.4 * color_sim, 3)


def image_url(item: Item) -> str | None:
    return f"/uploads/{os.path.basename(item.image_path)}" if item.image_path else None


# ---------- serialisation ----------
def serialize_claim(claim: Claim, viewer: User | None) -> dict:
    item_owner = claim.item.poster_id
    can_see = viewer is not None and viewer.id in (item_owner, claim.claimant_id)
    return {
        "id": claim.id,
        "claimantId": claim.claimant.public_id,
        "claimantName": claim.claimant_name if can_see else "A student",
        "details": claim.details if can_see else "",   # private detail: only owner + claimant
        "submittedAt": claim.submitted_at,
        "reviewedAt": claim.reviewed_at,
        "status": claim.status,
    }


def serialize_item(item: Item, viewer: User | None) -> dict:
    return {
        "id": item.id,
        "kind": item.kind,
        "title": item.title,
        "category": item.category,
        "description": item.description,
        "location": item.location,
        "eventAt": item.event_at,
        "reportedAt": item.reported_at,
        "updatedAt": item.updated_at,
        "status": item.status,
        "imageUrl": image_url(item),
        "imageName": item.image_name,
        "posterId": item.poster.public_id,
        "posterName": item.poster.name,
        "claims": [serialize_claim(c, viewer) for c in item.claims],
    }


# ---------- search ----------
RECENCY = {"today": timedelta(days=1), "week": timedelta(days=7), "month": timedelta(days=30)}


def search_items(db: Session, query: str = "", kind: str = "all", category: str = "all",
                 location: str = "all", recency: str = "all", claim_state: str = "all") -> list[Item]:
    q = db.query(Item)
    if kind in ("lost", "found"):
        q = q.filter(Item.kind == kind)
    if category and category != "all":
        q = q.filter(Item.category == category)
    if location and location != "all":
        q = q.filter(Item.location.ilike(f"%{location}%"))
    if recency in RECENCY:
        q = q.filter(Item.reported_at >= utcnow() - RECENCY[recency])
    if claim_state == "none":
        q = q.filter(~Item.claims.any())
    elif claim_state in ("pending", "approved"):
        q = q.filter(Item.claims.any(Claim.status == claim_state))
    if query and query.strip():
        like = f"%{query.strip()}%"
        q = q.filter(Item.title.ilike(like) | Item.description.ilike(like)
                     | Item.location.ilike(like) | Item.category.ilike(like))
    return q.order_by(Item.reported_at.desc()).all()


# ---------- matching ----------
def _words(text: str) -> set[str]:
    return {w for w in re.split(r"[^a-z0-9]+", text.lower()) if len(w) > 3}


def _spot(location: str) -> str:
    return re.split(r"[·,]", location.lower())[0].strip()


def score_pair(source: Item, cand: Item) -> tuple[float, str, float | None]:
    shared = _words(f"{source.title} {source.description}") & _words(f"{cand.title} {cand.description}")
    same_cat = source.category == cand.category
    same_spot = _spot(source.location) == _spot(cand.location)
    recent = abs(source.event_at - cand.event_at) < timedelta(days=7)
    text = min(0.97, 0.22 + 0.37 * same_cat + 0.24 * same_spot + 0.06 * min(len(shared), 4) + 0.07 * recent)

    img = image_similarity(source, cand)
    score = 0.55 * text + 0.45 * img if img is not None else text

    reasons = [r for r, ok in [
        ("similar photo", img is not None and img >= 0.6),
        ("same category", same_cat),
        ("nearby campus spot", same_spot),
        ("shared item details", bool(shared)),
    ] if ok]
    return round(min(score, 0.99), 3), " · ".join(reasons) or "related campus report", img


def find_matches(db: Session, source: Item, viewer: User | None, limit: int = 4, min_score: float = 0.35) -> dict:
    opposite = "found" if source.kind == "lost" else "lost"
    candidates = db.query(Item).filter(Item.kind == opposite, Item.status == "active", Item.id != source.id).all()
    used_images = False
    results = []
    for cand in candidates:
        score, reason, img = score_pair(source, cand)
        used_images |= img is not None
        if score >= min_score:
            results.append({"item": serialize_item(cand, viewer), "score": score, "reason": reason, "imageScore": img})
    results.sort(key=lambda m: m["score"], reverse=True)
    return {"mode": "image+text" if used_images else "text", "matches": results[:limit]}


# ---------- stats ----------
def board_stats(db: Session) -> dict:
    active = db.query(Item).filter(Item.status == "active")
    return {
        "active": active.count(),
        "found": active.filter(Item.kind == "found").count(),
        "lost": db.query(Item).filter(Item.status == "active", Item.kind == "lost").count(),
        "claims": db.query(Claim).filter(Claim.status == "pending").count(),
    }
