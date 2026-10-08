"""Business logic for items: image storage, image fingerprinting and matching.

"AI image similarity" here is lightweight and runs on any laptop (no GPU, no model download):
  * perceptual hash (pHash)  -> catches the same object photographed again
  * colour histogram         -> catches "black earbuds case" vs "black earbuds case"
  * text similarity          -> title + description + category
Combined into one 0..1 score. Swap `image_similarity` for CLIP embeddings later if you have time.
"""
import json
import os
import uuid
from difflib import SequenceMatcher

import imagehash
from fastapi import HTTPException, UploadFile
from PIL import Image
from sqlalchemy.orm import Session

from models.item import Item, ItemOut, ItemStatus, ItemType, MatchOut

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024

os.makedirs(UPLOAD_DIR, exist_ok=True)


# ---------- image storage & fingerprinting ----------
async def save_image(file: UploadFile) -> tuple[str, str, str]:
    """Saves the upload, returns (path, phash, colour signature)."""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, "Image must be JPEG, PNG or WEBP")
    data = await file.read()
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(400, "Image too large (max 5 MB)")

    ext = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[file.content_type]
    path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}{ext}")
    with open(path, "wb") as f:
        f.write(data)

    try:
        img = Image.open(path).convert("RGB")
    except Exception:
        os.remove(path)
        raise HTTPException(400, "Could not read image")

    phash = str(imagehash.phash(img))
    return path, phash, json.dumps(color_signature(img))


def color_signature(img: Image.Image, bins: int = 4) -> list[float]:
    """Normalised RGB histogram with bins^3 buckets."""
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
    # pHash: 64 bits, distance 0 = identical
    dist = imagehash.hex_to_hash(a.image_hash) - imagehash.hex_to_hash(b.image_hash)
    hash_sim = max(0.0, 1 - dist / 32)
    color_sim = 0.0
    if a.color_sig and b.color_sig:
        ca, cb = json.loads(a.color_sig), json.loads(b.color_sig)
        color_sim = sum(min(x, y) for x, y in zip(ca, cb))  # histogram intersection
    return round(0.6 * hash_sim + 0.4 * color_sim, 3)


def text_similarity(a: Item, b: Item) -> float:
    ta = f"{a.title} {a.description}".lower()
    tb = f"{b.title} {b.description}".lower()
    seq = SequenceMatcher(None, ta, tb).ratio()
    wa, wb = set(ta.split()), set(tb.split())
    jacc = len(wa & wb) / len(wa | wb) if wa | wb else 0
    cat = 1.0 if a.category == b.category else 0.0
    return round(0.35 * seq + 0.35 * jacc + 0.3 * cat, 3)


# ---------- queries ----------
def to_out(item: Item, base_url: str = "") -> ItemOut:
    out = ItemOut.model_validate(item)
    if item.image_path:
        out.image_url = f"{base_url}/uploads/{os.path.basename(item.image_path)}"
    return out


def search_items(
    db: Session,
    q: str | None = None,
    type: ItemType | None = None,
    category: str | None = None,
    location: str | None = None,
    status: ItemStatus | None = ItemStatus.open,
    limit: int = 20,
    offset: int = 0,
) -> list[Item]:
    query = db.query(Item)
    if type:
        query = query.filter(Item.type == type)
    if category:
        query = query.filter(Item.category == category)
    if status:
        query = query.filter(Item.status == status)
    if location:
        query = query.filter(Item.location.ilike(f"%{location}%"))
    if q:
        like = f"%{q}%"
        query = query.filter((Item.title.ilike(like)) | (Item.description.ilike(like)))
    return query.order_by(Item.event_time.desc()).offset(offset).limit(limit).all()


def find_matches(db: Session, item: Item, limit: int = 5, min_score: float = 0.3) -> list[MatchOut]:
    """For a LOST item, rank open FOUND items (and vice versa)."""
    opposite = ItemType.found if item.type == ItemType.lost else ItemType.lost
    candidates = db.query(Item).filter(Item.type == opposite, Item.status == ItemStatus.open).all()

    results = []
    for c in candidates:
        img = image_similarity(item, c)
        txt = text_similarity(item, c)
        score = 0.6 * img + 0.4 * txt if img is not None else txt
        if score >= min_score:
            results.append(MatchOut(item=to_out(c), score=round(score, 3), image_score=img, text_score=txt))
    results.sort(key=lambda m: m.score, reverse=True)
    return results[:limit]

