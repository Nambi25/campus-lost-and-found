"""
FoundIt AI pipeline - step 2: text and image embeddings (OpenCLIP).

One model embeds BOTH text and images into the same space, so a text query like
"something to charge my phone" can be compared directly with a photo of a power bank.
Vectors are L2-normalised, so cosine similarity == dot product.

The first call downloads the model weights (~600 MB). Run `python -m ai.embeddings`
once NOW to warm it up, before the demo and before the Wi-Fi gets busy.
"""
from __future__ import annotations

from functools import lru_cache

MODEL_NAME = "ViT-B-32"
PRETRAINED = "laion2b_s34b_b79k"


@lru_cache(maxsize=1)
def _load():
    """Load the model once per process (slow the first time, instant after)."""
    import open_clip
    import torch

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, _, preprocess = open_clip.create_model_and_transforms(
        MODEL_NAME, pretrained=PRETRAINED, device=device
    )
    model.eval()
    tokenizer = open_clip.get_tokenizer(MODEL_NAME)
    return torch, model, preprocess, tokenizer, device


def embed_text(text: str) -> list[float]:
    """Short text -> normalised vector. Keep text under ~70 words (CLIP limit is 77 tokens)."""
    torch, model, _, tokenizer, device = _load()
    tokens = tokenizer([text]).to(device)
    with torch.no_grad():
        vec = model.encode_text(tokens)
        vec = vec / vec.norm(dim=-1, keepdim=True)
    return vec[0].cpu().tolist()


def embed_image(image_path: str) -> list[float]:
    """Image file -> normalised vector."""
    from PIL import Image

    torch, model, preprocess, _, device = _load()
    image = preprocess(Image.open(image_path).convert("RGB")).unsqueeze(0).to(device)
    with torch.no_grad():
        vec = model.encode_image(image)
        vec = vec / vec.norm(dim=-1, keepdim=True)
    return vec[0].cpu().tolist()


def item_text(fields: dict) -> str:
    """Turn describe_item() output into one short sentence for text embedding.

    Uses ONLY public fields, so private details never end up in a search index.
    """
    parts = [
        fields.get("color"),
        fields.get("title"),
        fields.get("category") if fields.get("category") != "other" else None,
        fields.get("brand"),
        fields.get("public_description"),
    ]
    return ", ".join(str(p) for p in parts if p)[:300]


def embed_item(fields: dict, image_path: str | None = None) -> dict:
    """Everything B needs to store for one item: {"text_vec": [...], "image_vec": [...] or None}."""
    return {
        "text_vec": embed_text(item_text(fields)),
        "image_vec": embed_image(image_path) if image_path else None,
    }


if __name__ == "__main__":
    # Warm-up + sanity check: downloads weights, then prints vector sizes.
    v = embed_text("black earbud case")
    print(f"OK: model loaded, text vector has {len(v)} dimensions")
