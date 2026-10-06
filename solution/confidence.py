import pandas as pd


def calculate_confidence(ranked: pd.DataFrame) -> float:
    """
    Calculate confidence from the top candidate and
    the gap between the first and second candidate.
    """

    if ranked.empty:
        return 0.0

    top1 = float(ranked.iloc[0]["hybrid_score"])

    if len(ranked) == 1:
        margin = top1
    else:
        top2 = float(ranked.iloc[1]["hybrid_score"])
        margin = max(0.0, top1 - top2)

    # Normalize margin so it contributes reasonably.
    margin_score = min(margin / 0.20, 1.0)

    confidence = (
        top1 * 0.70
        + margin_score * 0.30
    )

    return max(0.0, min(1.0, confidence))