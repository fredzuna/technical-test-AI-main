import re
import unicodedata


def normalize_text(text: str) -> str:
    text = str(text or "").lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(
        c for c in text
        if not unicodedata.combining(c)
    )
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())