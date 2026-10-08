# Single source of truth for item categories. describe.py and match.py both import this.

# category: hint for Gemma (what it is, and what to look at to tell two of them apart)
CATEGORY_HINTS = {
    "id_card": "student/college ID, library card, bus pass, any card with a name or photo",
    "wallet": "wallet, card holder, purse, money pouch",
    "keys": "keys, keychains, key fobs, hostel/room keys",
    "phone": "mobile phone or phone with a case",
    "earbuds": "earbuds, earphones, AirPods and their charging case",
    "headphones": "over-ear or on-ear headphones, headsets, neckbands",
    "charger": "phone/laptop chargers, adapters, cables",
    "power_bank": "power banks",
    "laptop": "laptop or tablet",
    "laptop_accessory": "mouse, keyboard, laptop sleeve, stand, webcam",
    "usb_drive": "pen drive, USB stick, memory card, hard disk",
    "calculator": "scientific/graphing calculators",
    "watch": "wrist watch, smartwatch, fitness band (note strap, dial colour, case colour)",
    "spectacles": "prescription glasses, spectacles, spectacle case (note frame shape, colour, rimless or not)",
    "sunglasses": "sunglasses",
    "bottle": "water bottle, flask, sipper (note material, size, colour, stickers, dents)",
    "lunchbox": "lunch box, tiffin, food container",
    "umbrella": "umbrellas and raincoats",
    "bag": "backpack, sling bag, tote, laptop bag, pouch",
    "book": "textbooks, novels, lab manuals, record books",
    "notebook": "notebooks, diaries, folders, files, loose papers",
    "stationery": "pens, geometry box, drafter, pencil case, highlighters",
    "clothing": "jackets, hoodies, lab coats, scarves, caps, gloves",
    "shoes": "shoes, sandals, slippers",
    "jewellery": "rings, chains, bracelets, earrings, anklets",
    "sports_gear": "badminton racket, ball, shuttle, gym gloves, jersey, skates",
    "musical_item": "guitar picks, small instruments, tuner",
    "other": "anything that fits none of the above",
}

CATEGORIES = list(CATEGORY_HINTS.keys())

# Gemma may say "glasses" or "pendrive"; map near-misses to our names
ALIASES = {
    "earphones": "earbuds", "airpods": "earbuds", "earbud_case": "earbuds", "earbuds_case": "earbuds",
    "glasses": "spectacles", "eyeglasses": "spectacles", "spectacle": "spectacles",
    "smartwatch": "watch", "watches": "watch", "wristwatch": "watch",
    "water_bottle": "bottle", "flask": "bottle", "sipper": "bottle",
    "tiffin": "lunchbox", "lunch_box": "lunchbox",
    "pendrive": "usb_drive", "pen_drive": "usb_drive", "hard_disk": "usb_drive",
    "powerbank": "power_bank", "tablet": "laptop", "mouse": "laptop_accessory",
    "id": "id_card", "idcard": "id_card", "card": "id_card",
    "pen": "stationery", "pencil_case": "stationery", "geometry_box": "stationery",
    "jacket": "clothing", "hoodie": "clothing", "cap": "clothing",
    "backpack": "bag", "purse": "wallet", "shoe": "shoes", "slippers": "shoes",
    "ring": "jewellery", "jewelry": "jewellery",
}

# Categories the model could reasonably confuse; match_item treats these as the same pool
GROUPS = [
    {"earbuds", "headphones"},
    {"spectacles", "sunglasses"},
    {"charger", "power_bank"},
    {"book", "notebook"},
    {"wallet", "id_card"},
    {"laptop", "laptop_accessory"},
]

def normalize_category(value):
    v = str(value or "").strip().lower().replace(" ", "_").replace("-", "_")
    if v in CATEGORY_HINTS:
        return v
    return ALIASES.get(v, "other")

def categories_compatible(a, b):
    if a == b or "other" in (a, b):
        return True
    return any(a in g and b in g for g in GROUPS)

def prompt_block():
    return "\n".join(f"- {c}: {h}" for c, h in CATEGORY_HINTS.items())
