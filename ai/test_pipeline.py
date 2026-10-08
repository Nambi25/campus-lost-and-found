"""
End-to-end test with REAL models: photos -> Gemma description -> CLIP vectors -> similarity table.
Run from the repo root (venv active, GEMINI_API_KEY set):
    python -m ai.test_pipeline a.jpg b.jpg c.jpg --query "something to charge my phone"
Tip: include TWO photos of the same object from different angles, plus a few other objects.
"""
import argparse

from .describe import describe_item
from .embeddings import embed_item
from .match import search
from .similarity import cosine


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("images", nargs="+")
    ap.add_argument("--query", default=None)
    args = ap.parse_args()

    items = []
    for i, path in enumerate(args.images):
        print(f"[{i}] describing {path} ...")
        fields = describe_item(path)
        vecs = embed_item(fields, path)
        item = {"id": i, "type": "found", **fields, **vecs, "path": path}
        items.append(item)
        print(f"    -> {fields['category']}: {fields['title']} ({fields['color']})")
        print(f"       public: {fields['public_description']}")
        print(f"       private (never show): {fields['private_details']}")

    print("\nImage-image similarity (same object should be clearly higher than the rest):")
    print("      " + "".join(f"[{j}]    " for j in range(len(items))))
    for i, a in enumerate(items):
        row = "".join(f"{cosine(a['image_vec'], b['image_vec']):.2f}   " for b in items)
        print(f"[{i}]   {row}")

    if args.query:
        print(f"\nSearch: {args.query!r}")
        for r in search(args.query, items, k=5):
            it = items[r["id"]]
            print(f"  {r['score']:.2f}  [{it['id']}] {it['title']}  ({it['path']})")


if __name__ == "__main__":
    main()
