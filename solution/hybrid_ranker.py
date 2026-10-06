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
