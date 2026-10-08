# CampusFind — Backend (FastAPI)

Backend for the CampusFind React frontend (`/frontend`). Every response is in the exact shape
`frontend/src/services/api.js` reads, so pages and components need no changes.

## Run it (Windows)
```powershell
cd backend
py -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
python seed.py                         # optional: 6 demo reports so the board isn't empty
python -m uvicorn main:app --reload
```
API docs: **http://localhost:8000/docs** · Tests: `pytest -q`

Then in another terminal, start the frontend (port 3000). Vite proxies `/api` and `/uploads` to port 8000.

SQLite by default (`campusfind.db`). For Supabase/Postgres set `DATABASE_URL=postgresql+psycopg2://...`.

## Structure
```
main.py                   app, CORS, /uploads, routers under /api
database.py               engine + session
models/                   tables + response shapes (user, item, claim)
routes/users.py           identity (X-User-Id header or bearer token), register/login/me
routes/items.py           list/search, create, details, matches, stats, my items, status, search-by-image
routes/claims.py          submit claim, approve/reject
services/item_service.py  photo storage + fingerprint, serialisation, search, matching, stats
seed.py                   demo data
```

## Identity
The frontend has no login page, so each browser keeps a random id in localStorage and sends
`X-User-Id` (plus `X-User-Name` once known). The backend creates that user on first use.
Fine for a demo. Before real use, add the login page; email/password + bearer token is already supported
(`/api/users/register`, `/api/users/login`).

## Endpoints (all under `/api`)
| Method | Path | Used by |
|---|---|---|
| GET | /items?query&kind&category&location&recency&claimState | Home feed + filters |
| GET | /items/stats | Home counters |
| POST | /items (FormData: kind,title,category,description,location,timestamp,image) | Report lost/found |
| GET | /items/{id} | Item details |
| GET | /items/{id}/matches → {mode, matches:[{item,score,reason,imageScore}]} | Suggested matches |
| PATCH | /items/{id}/status {status: active\|resolved} | My items (owner only) |
| DELETE | /items/{id} | owner only |
| POST | /items/{id}/claims {claimantName, details} | "I think this is mine" |
| PATCH | /items/{id}/claims/{claimId} {status: approved\|rejected} | Owner review |
| GET | /items/mine → {reports, claims} | My items |
| POST | /items/search-by-image (FormData: image, kind, category) | bonus: find by photo |
| GET | /items/categories | dropdown values |

## Claim verification
The claimant submits a private detail that isn't in the public description. Only the report owner
(and the claimant) can see it; everyone else sees just "A student · pending". The owner approves or rejects;
approving one claim auto-rejects the other pending ones. The owner marks the report resolved after the handoff.

## Matching
Score = text signals (category, same campus spot, shared words, found within 7 days) blended with photo
similarity (perceptual hash + colour histogram) when both reports have photos. Runs on any laptop, no GPU.
Upgrade path: replace `image_similarity()` with CLIP embeddings.
