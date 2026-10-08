"""Claim verification flow.

1. Owner sees a FOUND item -> POST /claims with answer to the finder's secret question + proof.
2. Finder reviews claims on their item -> approve / reject.
   Approving generates a 6-digit handover code (shown only to the claimant)
   and auto-rejects the other pending claims.
3. At the physical handover the claimant tells the finder the code ->
   finder POSTs it to /claims/{id}/complete -> item becomes "returned".
"""
import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.claim import Claim, ClaimCreate, ClaimOut, ClaimStatus, HandoverConfirm
from models.item import Item, ItemStatus, ItemType
from models.user import User
from routes.users import get_current_user

router = APIRouter(prefix="/claims", tags=["claims"])


def _out(claim: Claim, viewer: User) -> ClaimOut:
    out = ClaimOut.model_validate(claim)
    out.claimant_name = claim.claimant.name if claim.claimant else None
    if claim.claimant_id != viewer.id:      # finder must NOT see the code
        out.handover_code = None
    return out


def _get_claim_for_finder(db: Session, claim_id: int, user: User) -> Claim:
    claim = db.get(Claim, claim_id)
    if not claim:
        raise HTTPException(404, "Claim not found")
    if claim.item.reporter_id != user.id:
        raise HTTPException(403, "Only the finder can review this claim")
    return claim


@router.post("", response_model=ClaimOut, status_code=201)
def create_claim(body: ClaimCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.get(Item, body.item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    if item.type != ItemType.found:
        raise HTTPException(400, "You can only claim FOUND items")
    if item.status != ItemStatus.open:
        raise HTTPException(400, "Item is no longer available")
    if item.reporter_id == user.id:
        raise HTTPException(400, "You can't claim your own post")
    if item.verification_question and not body.answer.strip():
        raise HTTPException(400, "Answer the verification question")
    existing = db.query(Claim).filter(
        Claim.item_id == item.id, Claim.claimant_id == user.id, Claim.status == ClaimStatus.pending
    ).first()
    if existing:
        raise HTTPException(400, "You already have a pending claim on this item")

    claim = Claim(item_id=item.id, claimant_id=user.id, answer=body.answer.strip(),
                  proof_details=body.proof_details.strip())
    db.add(claim)
    db.commit()
    db.refresh(claim)
    return _out(claim, user)


@router.get("/mine", response_model=list[ClaimOut])
def my_claims(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Claims I made (includes my handover codes once approved)."""
    claims = db.query(Claim).filter(Claim.claimant_id == user.id).order_by(Claim.created_at.desc()).all()
    return [_out(c, user) for c in claims]


@router.get("/item/{item_id}", response_model=list[ClaimOut])
def claims_for_item(item_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Finder reviews all claims on their found item."""
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    if item.reporter_id != user.id:
        raise HTTPException(403, "Only the finder can see claims on this item")
    return [_out(c, user) for c in item.claims]


@router.post("/{claim_id}/approve", response_model=ClaimOut)
def approve_claim(claim_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    claim = _get_claim_for_finder(db, claim_id, user)
    if claim.status != ClaimStatus.pending:
        raise HTTPException(400, f"Claim is already {claim.status.value}")

    claim.status = ClaimStatus.approved
    claim.handover_code = f"{secrets.randbelow(10**6):06d}"
    claim.resolved_at = datetime.utcnow()
    claim.item.status = ItemStatus.claimed
    for other in claim.item.claims:
        if other.id != claim.id and other.status == ClaimStatus.pending:
            other.status = ClaimStatus.rejected
            other.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(claim)
    return _out(claim, user)


@router.post("/{claim_id}/reject", response_model=ClaimOut)
def reject_claim(claim_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    claim = _get_claim_for_finder(db, claim_id, user)
    if claim.status != ClaimStatus.pending:
        raise HTTPException(400, f"Claim is already {claim.status.value}")
    claim.status = ClaimStatus.rejected
    claim.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(claim)
    return _out(claim, user)


@router.post("/{claim_id}/complete", response_model=ClaimOut)
def complete_handover(
    claim_id: int, body: HandoverConfirm,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    """Finder enters the code the claimant shows them at pickup."""
    claim = _get_claim_for_finder(db, claim_id, user)
    if claim.status != ClaimStatus.approved:
        raise HTTPException(400, "Claim must be approved first")
    if not secrets.compare_digest(body.handover_code.strip(), claim.handover_code or ""):
        raise HTTPException(400, "Wrong handover code")
    claim.status = ClaimStatus.completed
    claim.item.status = ItemStatus.returned
    db.commit()
    db.refresh(claim)
    return _out(claim, user)

