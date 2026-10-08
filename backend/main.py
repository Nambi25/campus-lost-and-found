"""CampusFind — Campus Lost & Found backend (FastAPI).

Run:   python -m uvicorn main:app --reload
Docs:  http://localhost:8000/docs
All endpoints live under /api  (the frontend's Vite dev server proxies /api and /uploads here).
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import models  # noqa: F401  (registers tables)
from database import Base, engine
from routes import claims, items, users
from services.item_service import UPLOAD_DIR

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CampusFind API", version="2.0.0",
              description="Campus Lost & Found — report, search, AI-match and claim items.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(users.router, prefix="/api")
app.include_router(items.router, prefix="/api")
app.include_router(claims.router, prefix="/api")


@app.get("/api/health", tags=["health"])
@app.get("/", include_in_schema=False)
def health():
    return {"status": "ok", "docs": "/docs"}
