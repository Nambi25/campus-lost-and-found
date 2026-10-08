"""
Offline test of matching/search logic using fake vectors (no models, no internet).
Run from the repo root:   python -m ai.test_match_offline
"""
from .match import match_item, pair_score, search


def unit(*xs):
    n = sum(x * x for x in xs) ** 0.5
    return [x / n for x in xs]


earbuds_lost = {"id": 1, "type": "lost", "category": "earbuds", "image_vec": None,
                "text_vec": unit(1.0, 0.1, 0.0)}
earbuds_found = {"id": 2, "type": "found", "category": "earbuds",
                 "image_vec": unit(0.95, 0.05, 0.1), "text_vec": unit(0.9, 0.1, 0.1)}
bottle_found = {"id": 3, "type": "found", "category": "bottle",
                "image_vec": unit(0.0, 1.0, 0.1), "text_vec": unit(0.1, 1.0, 0.0)}
powerbank_found = {"id": 4, "type": "found", "category": "charger",
                   "image_vec": unit(0.0, 0.1, 1.0), "text_vec": unit(0.0, 0.1, 1.0)}
earbuds_found_2 = {"id": 5, "type": "found", "category": "earbuds",
                   "image_vec": unit(0.2, 0.9, 0.1), "text_vec": unit(0.3, 0.8, 0.1)}

pool = [earbuds_lost, earbuds_found, bottle_found, powerbank_found, earbuds_found_2]

m = match_item(earbuds_lost, pool, threshold=None)
print("match_item:", m)
assert m[0]["id"] == 2, "closest earbuds should rank first"
assert all(r["id"] not in (3, 4) for r in m), "different categories must be filtered out"
assert all(r["id"] != 1 for r in m), "an item must not match itself"

assert all(r["id"] == 1 for r in match_item(earbuds_found, pool, threshold=None))

s = search("something to charge my phone", pool, embed_query=lambda q: unit(0.0, 0.1, 1.0))
print("search:", s)
assert s[0]["id"] == 4, "power bank should rank first"

assert pair_score({"id": 9}, {"id": 10}) == 0.0
assert search("anything", []) == []

print("\nAll offline tests passed.")
