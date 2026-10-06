import numpy as np
import pandas as pd

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from embed_helper import embed_texts


def cosine_similarity(
    query_embedding: list[float],
    candidate_embeddings: list[list[float]],
) -> np.ndarray:

    query = np.array(query_embedding)

    candidates = np.array(candidate_embeddings)

    query_norm = np.linalg.norm(query)

    candidate_norms = np.linalg.norm(
        candidates,
        axis=1,
    )

    return (
        candidates @ query
    ) / (
        candidate_norms * query_norm
    )


def build_catalog_text(row: pd.Series) -> str:
    """
    Text representation used for catalog embeddings.
    """

    return " ".join(
        value
        for value in [
            row.get("manufacturer", ""),
            row.get("submodel", ""),
            row.get("descveh", ""),
            row.get("tipveh", ""),
            row.get("cvesegm", ""),
        ]
        if value
    )


def build_query_text(query):
    values = [
        query.get("description"),
        query.get("marca"),
        query.get("submarca"),
        query.get("tipveh"),
        query.get("segment"),
        query.get("year"),
    ]

    return " ".join(
        str(value).strip()
        for value in values
        if pd.notna(value) and str(value).strip()
    )


def rank_by_embedding(
    query: pd.Series,
    candidates: pd.DataFrame,
) -> pd.DataFrame:

    query_text = build_query_text(query)

    candidate_texts = [
        build_catalog_text(row)
        for _, row in candidates.iterrows()
    ]

    query_embedding = embed_texts(
        [query_text]
    )[0]

    candidate_embeddings = embed_texts(
        candidate_texts
    )

    candidates = candidates.copy()

    candidates["embedding_score"] = cosine_similarity(
        query_embedding,
        candidate_embeddings,
    )

    return candidates.sort_values(
        "embedding_score",
        ascending=False,
    ).reset_index(drop=True)