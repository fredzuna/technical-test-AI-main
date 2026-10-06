"""Cached batch embedding, so you do not spend an hour of the five on plumbing.

Deliberately unopinionated about WHAT you embed. Choosing the text that
represents a catalog row is part of the exercise, and it matters more than you
might expect. Look at the data before you decide.

    from embed_helper import embed_texts

    vectors = embed_texts(["...", "..."])          # list[list[float]]

Results are cached on disk under .embed_cache/ keyed by (model, text), so
re-running costs nothing. Delete the directory to force a refresh.

Requires OPENAI_API_KEY in the environment. If you prefer a different provider
or a local model, ignore this file entirely; nothing else depends on it.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

DEFAULT_MODEL = "text-embedding-3-large"
CACHE_DIR = Path(__file__).parent / ".embed_cache"
BATCH_SIZE = 256


def _cache_path(model: str, text: str) -> Path:
    digest = hashlib.sha256(f"{model}\x00{text}".encode("utf-8")).hexdigest()
    # Two-level fan-out keeps directory sizes sane at 70k+ entries.
    return CACHE_DIR / digest[:2] / f"{digest}.json"


def _read_cached(model: str, text: str) -> list[float] | None:
    path = _cache_path(model, text)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _write_cached(model: str, text: str, vector: list[float]) -> None:
    path = _cache_path(model, text)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(vector), encoding="utf-8")


def embed_texts(texts: list[str], model: str = DEFAULT_MODEL) -> list[list[float]]:
    """Embed texts, hitting the API only for entries not already cached.

    Order of the returned vectors matches the order of the input.
    """
    if not texts:
        return []

    results: dict[int, list[float]] = {}
    pending: list[tuple[int, str]] = []

    for index, text in enumerate(texts):
        cached = _read_cached(model, text)
        if cached is None:
            pending.append((index, text))
        else:
            results[index] = cached

    if pending:
        from openai import OpenAI

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        client = OpenAI(api_key=api_key)

        for start in range(0, len(pending), BATCH_SIZE):
            chunk = pending[start : start + BATCH_SIZE]
            response = client.embeddings.create(model=model, input=[text for _, text in chunk])
            for (index, text), item in zip(chunk, response.data, strict=True):
                vector = list(item.embedding)
                results[index] = vector
                _write_cached(model, text, vector)

    return [results[i] for i in range(len(texts))]
