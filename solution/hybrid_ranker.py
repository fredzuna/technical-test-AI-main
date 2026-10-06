import pandas as pd

from embedding_ranker import rank_by_embedding
from ranking import rank_candidates


def hybrid_rank(
    query: pd.Series,
    candidates: pd.DataFrame,
) -> pd.DataFrame:

    # Structured ranking
    structured = rank_candidates(
        query,
        candidates,
    )

    # Embedding ranking
    embedded = rank_by_embedding(
        query,
        candidates,
    )

    # Match scores back by vehicle code
    scores = structured[
        [
            "code",
            "rank_score",
        ]
    ].merge(
        embedded[
            [
                "code",
                "embedding_score",
            ]
        ],
        on="code",
        how="left",
    )

    result = candidates.merge(
        scores,
        on="code",
        how="left",
    )

    # Normalize structured score to approximately 0-1
    max_score = result["rank_score"].max()

    if max_score > 0:
        result["structured_normalized"] = (
            result["rank_score"] / max_score
        )
    else:
        result["structured_normalized"] = 0.0

    # Hybrid score
    result["hybrid_score"] = (
        result["structured_normalized"] * 0.60
        + result["embedding_score"] * 0.40
    )

    return result.sort_values(
        "hybrid_score",
        ascending=False,
    ).reset_index(drop=True)


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