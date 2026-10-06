import pandas as pd

from catalog import load_catalog
from retrieval import retrieve_candidates
from hybrid_ranker import hybrid_rank


def evaluate():

    catalog = load_catalog()

    queries = pd.read_csv(
        "data/queries_labeled.csv",
        dtype=str,
    ).fillna("")

    top1_correct = 0
    top3_correct = 0

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

        expected = query["expected_code"]

        top1 = ranked.iloc[0]["code"]

        top3 = ranked.head(3)["code"].tolist()

        if top1 == expected:
            top1_correct += 1

        if expected in top3:
            top3_correct += 1

    total = len(queries)

    print(f"Queries: {total}")

    print(
        f"Hybrid Top-1 accuracy: "
        f"{top1_correct / total:.4f}"
    )

    print(
        f"Hybrid Top-3 accuracy: "
        f"{top3_correct / total:.4f}"
    )


if __name__ == "__main__":
    evaluate()