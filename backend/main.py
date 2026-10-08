"""Campus Lost & Found — FastAPI backend.

Run:   uvicorn main:app --reload
Docs:  http://localhost:8000/docs   (interactive Swagger UI — great for the demo)
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

app = FastAPI(title="Campus Lost & Found API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(users.router)
app.include_router(items.router)
app.include_router(claims.router)


@app.get("/", tags=["health"])
def health():
    return {"status": "ok", "docs": "/docs"}
