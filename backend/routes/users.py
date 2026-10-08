"""Users & identity.

The CampusFind frontend has no login screen, so it identifies each browser with a random id
kept in localStorage and sends it as `X-User-Id` (and optionally `X-User-Name`).
The first request from a new id creates a guest user automatically.

Email/password accounts are also supported (register/login -> bearer token) for when you add
a login page later. Bearer token wins if both are sent.
"""
import hashlib
import hmac
import os
import re
import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from database import get_db
from models.user import TokenOut, User, UserCreate, UserLogin, UserOut

router = APIRouter(prefix="/users", tags=["users"])

bearer_scheme = HTTPBearer(auto_error=False)  # adds the "Authorize" button in /docs
CLIENT_ID_RE = re.compile(r"^[A-Za-z0-9_-]{6,64}$")


# ---------- password helpers ----------
def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str | None) -> bool:
    if not stored:
        return False
    salt_hex, digest_hex = stored.split("$")
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 100_000)
    return hmac.compare_digest(digest.hex(), digest_hex)


def user_out(user: User) -> UserOut:
    return UserOut(id=user.public_id, name=user.name, email=user.email)


# ---------- identity dependencies (import these in other routers) ----------
def get_optional_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    x_user_id: str | None = Header(default=None),
    x_user_name: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User | None:
    if creds:
        user = db.query(User).filter(User.token == creds.credentials.strip()).first()
        if not user:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
        return user
    if x_user_id:
        if not CLIENT_ID_RE.match(x_user_id):
            raise HTTPException(400, "Invalid X-User-Id")
        user = db.query(User).filter(User.public_id == x_user_id).first()
        if not user:
            user = User(public_id=x_user_id, name=(x_user_name or "Student").strip()[:100] or "Student")
            db.add(user)
            db.commit()
            db.refresh(user)
        elif x_user_name and x_user_name.strip() and user.name == "Student":
            user.name = x_user_name.strip()[:100]
            db.commit()
        return user
    return None


def get_current_user(user: User | None = Depends(get_optional_user)) -> User:
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Send X-User-Id header or a bearer token")
    return user


# ---------- routes ----------
@router.post("/register", response_model=TokenOut, status_code=201)
def register(body: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email.lower()).first():
        raise HTTPException(400, "Email already registered")
    user = User(name=body.name, email=body.email.lower(),
                password_hash=hash_password(body.password), token=secrets.token_hex(32))
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenOut(token=user.token, user=user_out(user))


@router.post("/login", response_model=TokenOut)
def login(body: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.lower()).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    user.token = secrets.token_hex(32)
    db.commit()
    return TokenOut(token=user.token, user=user_out(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user_out(user)
