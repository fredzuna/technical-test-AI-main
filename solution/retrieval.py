import re
import unicodedata

import pandas as pd

from catalog import load_catalog


def normalize_text(value: str) -> str:
    """Normalize text for matching."""

    if not value:
        return ""

    value = str(value).upper()

    # Remove accents
    value = unicodedata.normalize("NFKD", value)
    value = "".join(
        char for char in value
        if not unicodedata.combining(char)
    )

    # Replace punctuation with spaces
    value = re.sub(r"[^A-Z0-9]+", " ", value)

    # Normalize whitespace
    value = re.sub(r"\s+", " ", value).strip()

    return value


def tokenize(value: str) -> set[str]:
    return set(normalize_text(value).split())


def text_similarity(query: str, candidate: str) -> float:
    """
    Simple token-overlap similarity.

    Returns a value between 0 and 1.
    """

    query_tokens = tokenize(query)
    candidate_tokens = tokenize(candidate)

    if not query_tokens or not candidate_tokens:
        return 0.0

    intersection = query_tokens & candidate_tokens

    return len(intersection) / len(query_tokens)


def retrieve_candidates(
    query: pd.Series,
    catalog: pd.DataFrame,
    limit: int = 20,
) -> pd.DataFrame:

    description = query["description"]

    # Start with all catalog rows.
    candidates = catalog.copy()

    # ---------------------------------------------------------
    # 1. Build a searchable text representation
    # ---------------------------------------------------------

    candidates["search_text"] = (
        candidates["manufacturer"].fillna("")
        + " "
        + candidates["submodel"].fillna("")
        + " "
        + candidates["descveh"].fillna("")
    )

    # ---------------------------------------------------------
    # 2. Calculate text similarity
    # ---------------------------------------------------------

    candidates["text_score"] = candidates["search_text"].apply(
        lambda value: text_similarity(
            description,
            value,
        )
    )

    # ---------------------------------------------------------
    # 3. Year score
    # ---------------------------------------------------------

    query_year = str(query.get("year", "")).strip()

    if query_year:
        candidates["year_score"] = candidates["years"].apply(
            lambda years: (
                1.0
                if query_year in years
                else 0.0
            )
        )
    else:
        candidates["year_score"] = 0.0

    # ---------------------------------------------------------
    # 4. Segment score
    # ---------------------------------------------------------

    query_segment = normalize_text(
        query.get("segment", "")
    )

    candidates["segment_score"] = candidates[
        "cvesegm"
    ].apply(
        lambda value: (
            1.0
            if query_segment
            and normalize_text(value) == query_segment
            else 0.0
        )
    )

    # ---------------------------------------------------------
    # 5. Vehicle type score
    # ---------------------------------------------------------

    query_type = normalize_text(
        query.get("tipveh", "")
    )

    candidates["type_score"] = candidates[
        "tipveh"
    ].apply(
        lambda value: (
            1.0
            if query_type
            and normalize_text(value) == query_type
            else 0.0
        )
    )

    # ---------------------------------------------------------
    # 6. Combined retrieval score
    # ---------------------------------------------------------

    candidates["retrieval_score"] = (
        candidates["text_score"] * 0.60
        + candidates["year_score"] * 0.20
        + candidates["segment_score"] * 0.10
        + candidates["type_score"] * 0.10
    )

    # ---------------------------------------------------------
    # 7. Return top candidates
    # ---------------------------------------------------------

    return (
        candidates
        .sort_values(
            "retrieval_score",
            ascending=False,
        )
        .head(limit)
        .copy()
    )