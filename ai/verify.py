# backend/ai/verify.py
import json, os
import ollama

MODEL = os.environ.get("FOUNDIT_LOCAL_MODEL", "gemma4:e4b")

VERIFY_PROMPT = """
You are a lost-and-found matching assistant. 
Compare the primary target item image with the candidate item image.
Determine if they could be the same physical object based on distinct visual features (color shade, brand logo, marks, dial/strap style, damage).

Respond strictly in valid JSON format:
{
  "is_match": true/false,
  "confidence": 0.85,
  "reasoning": "Brief explanation comparing the key features."
}
"""

def verify_candidate_match(target_image_path: str, candidate_image_path: str) -> dict:
    """Passes two image paths to Gemma 4 to confirm whether they match."""
    try:
        resp = ollama.chat(
            model=MODEL,
            messages=[{
                "role": "user",
                "content": VERIFY_PROMPT,
                "images": [
                    os.path.expanduser(target_image_path),
                    os.path.expanduser(candidate_image_path)
                ]
            }],
            format="json",
            options={"temperature": 0.1}
        )
        content = resp["message"]["content"]
        start, end = content.find("{"), content.rfind("}")
        return json.loads(content[start:end + 1])
    except Exception as e:
        print(f"[AI Verify Error] {e}")
        return {"is_match": False, "confidence": 0.0, "reasoning": "Verification failed."}