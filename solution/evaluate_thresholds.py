import pandas as pd

from catalog import load_catalog
from retrieval import retrieve_candidates
from hybrid_ranker import hybrid_rank
from confidence import calculate_confidence


def challenge_score(
    correct_top1: bool,
    correct_in_top3: bool,
    decision: str,
) -> float:

    if decision == "auto_accept":
        return 1.0 if correct_top1 else -3.0

    return 0.15 if correct_in_top3 else -0.05


def evaluate_threshold(
    results: list[dict],
    threshold: float,
):

    total_score = 0.0
    auto_accepts = 0
    reviews = 0

    for result in results:

        confidence = result["confidence"]

        if confidence >= threshold:
            decision = "auto_accept"
            auto_accepts += 1
        else:
            decision = "review"
            reviews += 1

        total_score += challenge_score(
            result["correct_top1"],
            result["correct_in_top3"],
            decision,
        )

    return {
        "threshold": threshold,
        "score": total_score,
        "auto_accept": auto_accepts,
        "review": reviews,
        "average_score": total_score / len(results),
    }


def main():

    catalog = load_catalog()

    queries = pd.read_csv(
        "data/queries_labeled.csv",
        dtype=str,
    ).fillna("")

    results = []

    for _, query in queries.iterrows():

        candidates = retrieve_candidates(
            query,
            catalog,
            limit=20,
        )

        ranked = hybrid_rank(
            query,
            candidates,
        )

        confidence = calculate_confidence(
            ranked
        )

        expected = query["expected_code"]

        top1 = ranked.iloc[0]["code"]

        top3 = ranked.head(3)["code"].tolist()

        results.append({
            "query_id": query["query_id"],
            "confidence": confidence,
            "correct_top1": top1 == expected,
            "correct_in_top3": expected in top3,
        })

    print("\nThreshold evaluation\n")

    evaluations = []

    for threshold in [
        0.50,
        0.55,
        0.60,
        0.65,
        0.70,
        0.75,
        0.80,
        0.85,
        0.90,
        0.95,
    ]:

        result = evaluate_threshold(
            results,
            threshold,
        )

        evaluations.append(result)

    evaluation_df = pd.DataFrame(
        evaluations
    )

    print(
        evaluation_df.to_string(
            index=False
        )
    )

    best = evaluation_df.loc[
        evaluation_df["score"].idxmax()
    ]

    print("\nBEST THRESHOLD")

    print(best.to_string())


if __name__ == "__main__":
    main()