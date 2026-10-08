"""Offline describe_item using Ollama + Gemma 4. Same output contract as describe.py."""
import json, os

MODEL = os.environ.get("FOUNDIT_LOCAL_MODEL", "gemma4:e4b")


def _extract_json(text):
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON in model output")
    return json.loads(text[start:end + 1])


def describe_item_local(image_path):
    import ollama
    from ai.describe import SYSTEM_PROMPT, _normalize
    last_err = None
    for _ in range(2):
        try:
            resp = ollama.chat(
                model=MODEL,
                messages=[{"role": "user", "content": SYSTEM_PROMPT,
                           "images": [os.path.expanduser(image_path)]}],
                format="json",
                options={"temperature": 0.2},
            )
            data = _extract_json(resp["message"]["content"])
            out = _normalize(data)
            return out if out is not None else data
        except Exception as e:
            last_err = e
    raise last_err
