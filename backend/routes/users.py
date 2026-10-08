"""Users: register, login, current user.

Auth is a simple bearer token (good enough for a hackathon demo).
Frontend sends:  Authorization: Bearer <token>
If you switch to Supabase Auth later, only `get_current_user` needs changing.
"""
import hashlib
import hmac
import os
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from database import get_db
from models.user import TokenOut, User, UserCreate, UserLogin, UserOut

router = APIRouter(prefix="/users", tags=["users"])


# ---------- password helpers ----------
def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    salt_hex, digest_hex = stored.split("$")
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 100_000)
    return hmac.compare_digest(digest.hex(), digest_hex)


# ---------- auth dependency (import this in other routers) ----------
bearer_scheme = HTTPBearer(auto_error=False)  # adds the "Authorize" button in /docs


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not creds:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    token = creds.credentials.strip()
    user = db.query(User).filter(User.token == token).first()
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    return user


# ---------- routes ----------
@router.post("/register", response_model=TokenOut, status_code=201)
def register(body: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email.lower()).first():
        raise HTTPException(400, "Email already registered")
    user = User(
        name=body.name,
        email=body.email.lower(),
        roll_no=body.roll_no,
        phone=body.phone,
        password_hash=hash_password(body.password),
        token=secrets.token_hex(32),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenOut(token=user.token, user=UserOut.model_validate(user))


@router.post("/demo-login", response_model=TokenOut)
def demo_login(db: Session = Depends(get_db)):
    """Create or reset the fixed demo account so the demo button always works."""
    email = "demo@campusfind.app"
    password = "CampusFind123!"
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            name="Campus Student",
            email=email,
            roll_no=None,
            phone=None,
            password_hash=hash_password(password),
            token=secrets.token_hex(32),
        )
        db.add(user)
    else:
        user.password_hash = hash_password(password)
        user.token = secrets.token_hex(32)
        user.name = user.name or "Campus Student"
    db.commit()
    db.refresh(user)
    return TokenOut(token=user.token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenOut)
def login(body: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.lower()).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    user.token = secrets.token_hex(32)  # rotate on login
    db.commit()
    return TokenOut(token=user.token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
