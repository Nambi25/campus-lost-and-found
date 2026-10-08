"""Claim verification.

1. A student who thinks an item is theirs submits a claim with a private identifying detail
   (something NOT in the public description).
2. Only the report owner (and the claimant) can see that detail.
3. The owner approves or rejects. Approving one claim auto-rejects the other pending claims.
4. The owner marks the report "resolved" after the handoff (PATCH /items/{id}/status).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.claim import Claim, ClaimCreate, ClaimDecision
from models.item import Item, ItemOut
from models.user import User, utcnow
from routes.users import get_current_user
from services import item_service as svc

router = APIRouter(prefix="/items/{item_id}/claims", tags=["claims"])


def _get_item(db: Session, item_id: int) -> Item:
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(404, "This report is no longer available.")
    return item


@router.post("", response_model=ItemOut, status_code=201)
def create_claim(item_id: int, body: ClaimCreate, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    item = _get_item(db, item_id)
    if item.status == "resolved":
        raise HTTPException(400, "This item has already been marked resolved.")
    if item.poster_id == user.id:
        raise HTTPException(400, "You can't claim your own report.")
    if any(c.claimant_id == user.id and c.status == "pending" for c in item.claims):
        raise HTTPException(400, "You already have a pending claim on this report.")
    db.add(Claim(item_id=item.id, claimant_id=user.id,
                 claimant_name=body.claimantName.strip(), details=body.details.strip()))
    db.commit()
    db.refresh(item)
    return svc.serialize_item(item, user)


@router.patch("/{claim_id}", response_model=ItemOut)
def decide_claim(item_id: int, claim_id: int, body: ClaimDecision, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    if body.status not in ("approved", "rejected"):
        raise HTTPException(400, "Unsupported claim decision.")
    item = _get_item(db, item_id)
    if item.poster_id != user.id:
        raise HTTPException(403, "Only the report owner can review claims.")
    claim = next((c for c in item.claims if c.id == claim_id), None)
    if not claim:
        raise HTTPException(404, "This claim could not be found.")
    if claim.status != "pending":
        raise HTTPException(400, f"This claim was already {claim.status}.")

    now = utcnow()
    claim.status, claim.reviewed_at = body.status, now
    if body.status == "approved":
        for other in item.claims:
            if other.id != claim.id and other.status == "pending":
                other.status, other.reviewed_at = "rejected", now
    db.commit()
    db.refresh(item)
    return svc.serialize_item(item, user)
