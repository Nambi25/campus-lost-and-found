"""
Tuning test: does the system tell SAME objects from DIFFERENT objects (of the same category)?

Run from the repo root (venv active, GEMINI_API_KEY set):
    python -m ai.test_match ~/photos2/*.jpeg --same a1:a2 b1:b2

--same lists pairs of file names (without extension) that are the SAME physical object.
Results are cached in ~/.foundit_test_cache.json, so re-runs are instant (no Gemma calls).
"""
import argparse
import json
import os
from pathlib import Path

from .describe import describe_item
from .embeddings import embed_item
from .match import _same_kind, pair_score
from .similarity import cosine

CACHE = Path.home() / ".foundit_test_cache.json"


def load_cache() -> dict:
    try:
        return json.loads(CACHE.read_text())
    except Exception:
        return {}


def get_item(path: str, cache: dict) -> dict:
    key = f"{path}:{os.path.getmtime(path)}"
    if key not in cache:
        fields = describe_item(path)
        cache[key] = {**fields, **embed_item(fields, path)}
        CACHE.write_text(json.dumps(cache))
    return dict(cache[key])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("images", nargs="+")
    ap.add_argument("--same", nargs="*", default=[],
                    help="pairs that are the same object, e.g. a1:a2 b1:b2 (file names without extension)")
    args = ap.parse_args()

    cache = load_cache()
    items = []
    for i, p in enumerate(args.images):
        p = os.path.abspath(p)
        it = get_item(p, cache)
        it["id"], it["label"] = i, Path(p).stem
        items.append(it)
        print(f"[{i}] {it['label']}: {it['category']} | {it['title']} | color={it['color']} | brand={it['brand']}")

    n = len(items)

    def table(title, fn):
        print(f"\n{title}")
        print("        " + "".join(f"[{j}]   " for j in range(n)))
        for i in range(n):
            print(f"[{i}]    " + "".join(f"{fn(items[i], items[j]):.2f}  " for j in range(n)))

    table("IMAGE similarity", lambda a, b: cosine(a["image_vec"], b["image_vec"]))
    table("TEXT similarity", lambda a, b: cosine(a["text_vec"], b["text_vec"]))
    table("COMBINED score (this is what match_item uses)", pair_score)

    if not args.same:
        print("\nTip: add --same a1:a2 b1:b2 to get a threshold suggestion.")
        return

    same_pairs = {frozenset(spec.split(":")) for spec in args.same}
    same, diff = [], []
    for i in range(n):
        for j in range(i + 1, n):
            a, b = items[i], items[j]
            entry = (pair_score(a, b), a["label"], b["label"])
            if frozenset((a["label"], b["label"])) in same_pairs:
                same.append(entry)
            elif _same_kind(a, b):  # pairs from different categories are filtered out anyway
                diff.append(entry)

    print("\n=== Threshold check ===")
    if not same or not diff:
        print("Need at least one --same pair and one different-object pair in the same category.")
        return
    lo_same = min(same)
    hi_diff = max(diff)
    print(f"Lowest  SAME-object score:      {lo_same[0]:.3f}  ({lo_same[1]} vs {lo_same[2]})")
    print(f"Highest DIFFERENT-object score: {hi_diff[0]:.3f}  ({hi_diff[1]} vs {hi_diff[2]})")
    if lo_same[0] > hi_diff[0]:
        mid = (lo_same[0] + hi_diff[0]) / 2
        print(f"Separable. Suggested MATCH_THRESHOLD = {mid:.2f}  (margin {lo_same[0] - hi_diff[0]:.3f})")
    else:
        print("OVERLAP: a different object scores as high as a same object. "
              "Retake photos (plain background, same side, object closer) or change W_IMAGE/W_TEXT in match.py.")


if __name__ == "__main__":
    main()
