"""Fill the board with demo reports (same ones the frontend demo used).

Run once:   python seed.py
Re-running wipes old demo data first (only items posted by the demo students).
Replace these with REAL photos before the final demo for the best matching results.
"""
import io
import json
import os
import uuid
from datetime import timedelta

import imagehash
from PIL import Image, ImageDraw

import models  # noqa: F401
from database import Base, SessionLocal, engine
from models.claim import Claim
from models.item import Item
from models.user import User, utcnow
from services.item_service import UPLOAD_DIR, color_signature

Base.metadata.create_all(bind=engine)


def demo_image(bg, fg, shape):
    img = Image.new("RGB", (480, 360), bg)
    d = ImageDraw.Draw(img)
    if shape == "rect":
        d.rounded_rectangle((150, 70, 330, 290), 18, fill=fg)
        for r in range(4):
            for c in range(3):
                d.rectangle((175 + c * 50, 150 + r * 32, 205 + c * 50, 170 + r * 32), fill=bg)
    elif shape == "oval":
        d.ellipse((140, 100, 340, 260), fill=fg)
    elif shape == "bag":
        d.rectangle((130, 140, 350, 320), fill=fg)
        d.arc((180, 60, 300, 200), 180, 360, fill=fg, width=14)
    elif shape == "bottle":
        d.rectangle((205, 60, 275, 110), fill=(20, 20, 20))
        d.rounded_rectangle((180, 100, 300, 320), 30, fill=fg)
    else:
        d.rounded_rectangle((170, 120, 310, 240), 30, fill=fg)
    path = os.path.join(UPLOAD_DIR, f"seed-{uuid.uuid4().hex}.png")
    img.save(path)
    return path, str(imagehash.phash(img)), json.dumps(color_signature(img))


SEED = [
    # poster, kind, title, category, description, location, event hrs ago, reported hrs ago, image
    ("lee", "found", "Lime-green pencil pouch", "School supplies",
     "Small zip pouch with a white star patch. Found near the long tables after afternoon classes.",
     "Library · ground floor", 4, 2, ((38, 59, 56), (163, 255, 18), "pouch")),
    ("noah", "lost", "Graphite scientific calculator", "School supplies",
     "Dark grey graphing calculator with a tiny triangle sticker near the solar panel. Last used around the west lecture wing.",
     "West Hall · lecture wing", 27, 9, ((235, 235, 235), (60, 64, 72), "rect")),
    ("mira", "found", "Wireless earbud charging case", "Electronics",
     "White oval case, no earbuds inside. Picked up beside the student union charging counter.",
     "Student Union", 8, 6, ((52, 64, 74), (245, 245, 245), "oval")),
    ("rin", "found", "Canvas tote with blue notebook", "Bags & accessories",
     "Natural canvas tote with a blue spiral notebook. Found by the library north entrance; one stitched detail is being held back for verification.",
     "Library · north entrance", 31, 14, ((59, 51, 46), (222, 205, 170), "bag")),
    ("jules", "lost", "Forest-green water bottle", "Other",
     "Metal bottle with a black lid and a few small climbing-sticker marks. Might have been left after practice.",
     "Athletics Center", 52, 18, ((230, 230, 230), (34, 90, 60), "bottle")),
    ("rin", "found", "Graphing calculator", "School supplies",
     "Dark calculator picked up by a lecture-room seat. There is a tiny triangle sticker near the solar strip.",
     "West Hall · lecture wing", 22, 4, ((232, 232, 232), (58, 62, 70), "rect")),
]
NAMES = {"lee": "Lee", "noah": "Noah", "mira": "Mira S.", "rin": "Rin", "jules": "Jules"}

db = SessionLocal()
users = {}
for key, name in NAMES.items():
    pid = f"seed-student-{key}"
    u = db.query(User).filter(User.public_id == pid).first()
    if u:
        for it in list(u.items):
            if it.image_path and os.path.exists(it.image_path):
                os.remove(it.image_path)
            db.delete(it)
    else:
        u = User(public_id=pid, name=name)
        db.add(u)
    users[key] = u
db.commit()

now = utcnow()
created = {}
for poster, kind, title, cat, desc, loc, ev, rep, (bg, fg, shape) in SEED:
    path, ph, col = demo_image(bg, fg, shape)
    it = Item(kind=kind, title=title, category=cat, description=desc, location=loc,
              event_at=now - timedelta(hours=ev), reported_at=now - timedelta(hours=rep),
              image_path=path, image_name=os.path.basename(path), image_hash=ph, color_sig=col,
              poster_id=users[poster].id)
    db.add(it)
    created[title] = it
db.commit()

# one pending claim on the tote, like the frontend demo
db.add(Claim(item_id=created["Canvas tote with blue notebook"].id, claimant_id=users["mira"].id,
             claimant_name="Mira S.", details="There is a stitched wave on the inside pocket and a physics lab label on the notebook.",
             submitted_at=now - timedelta(hours=3)))
db.commit()
print(f"Seeded {len(SEED)} demo reports + 1 claim.")
db.close()
