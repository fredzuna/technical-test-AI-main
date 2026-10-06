from __future__ import annotations

import hashlib
import json
from pathlib import Path

import ollama


DEFAULT_MODEL = "nomic-embed-text"
CACHE_DIR = Path(__file__).parent / ".embed_cache"
BATCH_SIZE = 256


def _cache_path(model: str, text: str) -> Path:
    digest = hashlib.sha256(
        f"{model}\x00{text}".encode("utf-8")
    ).hexdigest()

    return CACHE_DIR / digest[:2] / f"{digest}.json"


def _read_cached(model: str, text: str) -> list[float] | None:
    path = _cache_path(model, text)

    if not path.exists():
        return None

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _write_cached(
    model: str,
    text: str,
    vector: list[float],
) -> None:
    path = _cache_path(model, text)
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(vector),
        encoding="utf-8",
    )


def embed_texts(
    texts: list[str],
    model: str = DEFAULT_MODEL,
) -> list[list[float]]:
    """Embed texts using Ollama, with disk caching."""

    if not texts:
        return []

    results: dict[int, list[float]] = {}
    pending: list[tuple[int, str]] = []

    # Check cache first
    for index, text in enumerate(texts):
        cached = _read_cached(model, text)

        if cached is None:
            pending.append((index, text))
        else:
            results[index] = cached

    # Generate missing embeddings
    if pending:
        for start in range(0, len(pending), BATCH_SIZE):
            chunk = pending[start:start + BATCH_SIZE]

            texts_to_embed = [
                text
                for _, text in chunk
            ]

            response = ollama.embed(
                model=model,
                input=texts_to_embed,
            )

            for (index, text), vector in zip(
                chunk,
                response["embeddings"],
                strict=True,
            ):
                vector = list(vector)

                results[index] = vector
                _write_cached(
                    model,
                    text,
                    vector,
                )

    # Preserve original input order
    return [
        results[i]
        for i in range(len(texts))
    ]