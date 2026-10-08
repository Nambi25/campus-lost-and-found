"""End-to-end test of the API exactly as the frontend uses it.   Run:  pytest -q"""
import io
import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["UPLOAD_DIR"] = "test_uploads"
if os.path.exists("test.db"):
    os.remove("test.db")

from fastapi.testclient import TestClient  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

from main import app  # noqa: E402

client = TestClient(app)
FINDER = {"X-User-Id": "browser-finder01", "X-User-Name": "Finder"}
OWNER = {"X-User-Id": "browser-owner001"}
OTHER = {"X-User-Id": "browser-other001"}


def photo(bg, fg=(255, 255, 255), shift=0):
    img = Image.new("RGB", (200, 200), bg)
    ImageDraw.Draw(img).ellipse((50 + shift, 60, 150 + shift, 140), fill=fg)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    return buf


def post_item(headers, kind, title, category, location, description, img=None):
    files = {"image": ("p.png", img, "image/png")} if img else None
    r = client.post("/api/items", headers=headers, files=files, data={
        "kind": kind, "title": title, "category": category, "location": location,
        "description": description, "timestamp": "2026-10-08T10:30"})
    assert r.status_code == 201, r.text
    return r.json()


def test_full_flow():
    # found item needs a photo
    r = client.post("/api/items", headers=FINDER, data={"kind": "found", "title": "Thing", "category": "Other",
                                                        "location": "Library", "description": "twelve chars here"})
    assert r.status_code == 400

    found = post_item(FINDER, "found", "Black earbuds case", "Electronics", "Library · 2nd floor",
                      "Black case found near the window desks", photo((10, 10, 10)))
    assert found["posterId"] == "browser-finder01" and found["posterName"] == "Finder"
    assert found["imageUrl"].startswith("/uploads/") and found["status"] == "active" and found["claims"] == []
    assert client.get(found["imageUrl"]).status_code == 200

    post_item(FINDER, "found", "Blue water bottle", "Other", "Canteen",
              "Steel bottle with a dent on the bottom", photo((20, 60, 200), (200, 200, 0)))
    lost = post_item(OWNER, "lost", "Lost black earbuds case", "Electronics", "Library",
                     "Black earbuds case with a small dent", photo((12, 12, 12), shift=5))

    # matches
    m = client.get(f"/api/items/{lost['id']}/matches").json()
    assert m["mode"] == "image+text" and m["matches"][0]["item"]["id"] == found["id"], m
    assert "similar photo" in m["matches"][0]["reason"]

    # search & filters (frontend param names)
    assert len(client.get("/api/items", params={"query": "earbuds"}).json()) == 2
    assert len(client.get("/api/items", params={"kind": "found", "location": "Library"}).json()) == 1
    assert len(client.get("/api/items", params={"recency": "today", "claimState": "none"}).json()) == 3
    assert client.get("/api/items/stats").json() == {"active": 3, "found": 2, "lost": 1, "claims": 0}

    # claims
    assert client.post(f"/api/items/{found['id']}/claims", headers=FINDER,
                       json={"claimantName": "Me", "details": "it's my own report"}).status_code == 400
    r = client.post(f"/api/items/{found['id']}/claims", headers=OWNER,
                    json={"claimantName": "Owner", "details": "Yellow smiley sticker inside the lid"})
    assert r.status_code == 201 and r.json()["claims"][0]["details"].startswith("Yellow")
    client.post(f"/api/items/{found['id']}/claims", headers=OTHER,
                json={"claimantName": "Imposter", "details": "It is mine, it is black"})
    assert client.post(f"/api/items/{found['id']}/claims", headers=OWNER,
                       json={"claimantName": "Owner", "details": "duplicate claim text"}).status_code == 400

    # privacy: a third party can't read claim details
    public = client.get(f"/api/items/{found['id']}").json()
    assert all(c["details"] == "" for c in public["claims"])
    finder_view = client.get(f"/api/items/{found['id']}", headers=FINDER).json()
    assert all(c["details"] for c in finder_view["claims"])
    assert client.get("/api/items/stats").json()["claims"] == 2
    assert len(client.get("/api/items", params={"claimState": "pending"}).json()) == 1

    # only owner reviews; approve one -> others rejected
    owner_claim = next(c for c in finder_view["claims"] if c["claimantId"] == "browser-owner001")
    url = f"/api/items/{found['id']}/claims/{owner_claim['id']}"
    assert client.patch(url, headers=OWNER, json={"status": "approved"}).status_code == 403
    item = client.patch(url, headers=FINDER, json={"status": "approved"}).json()
    assert sorted(c["status"] for c in item["claims"]) == ["approved", "rejected"]

    # my items
    mine = client.get("/api/items/mine", headers=OWNER).json()
    assert len(mine["reports"]) == 1 and mine["claims"][0]["status"] == "approved"
    assert mine["claims"][0]["itemTitle"] == "Black earbuds case"
    assert len(client.get("/api/items/mine", headers=FINDER).json()["reports"]) == 2

    # resolve
    assert client.patch(f"/api/items/{found['id']}/status", headers=OWNER, json={"status": "resolved"}).status_code == 403
    assert client.patch(f"/api/items/{found['id']}/status", headers=FINDER, json={"status": "resolved"}).json()["status"] == "resolved"
    assert client.post(f"/api/items/{found['id']}/claims", headers=OTHER,
                       json={"claimantName": "Late", "details": "too late to claim it"}).status_code == 400

    # search by photo
    r = client.post("/api/items/search-by-image", files={"image": ("q.png", photo((10, 10, 10)), "image/png")},
                    data={"kind": "lost", "category": "Electronics"})
    assert r.json()[0]["item"]["id"] == lost["id"]

    # account auth still works
    r = client.post("/api/users/register", json={"name": "A", "email": "a@college.edu", "password": "secret123"})
    tok = {"Authorization": f"Bearer {r.json()['token']}"}
    assert client.get("/api/users/me", headers=tok).status_code == 200
    assert client.post("/api/items", data={"kind": "lost"}).status_code in (401, 422)
