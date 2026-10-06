from confidence import calculate_confidence


def make_decision(
    ranked,
    threshold: float,
):
    confidence = calculate_confidence(ranked)

    top1_code = ranked.iloc[0]["code"]

    top3_codes = ranked.head(3)["code"].tolist()

    decision = (
        "auto_accept"
        if confidence >= threshold
        else "review"
    )

    return {
        "top1_code": top1_code,
        "top3_codes": "|".join(top3_codes),
        "confidence": confidence,
        "decision": decision,
    }