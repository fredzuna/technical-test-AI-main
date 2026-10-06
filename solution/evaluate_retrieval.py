import pandas as pd

from catalog import load_catalog
from retrieval import retrieve_candidates


def evaluate(k: int = 20):

    catalog = load_catalog()

    queries = pd.read_csv(
        "data/queries_labeled.csv",
        dtype=str,
    ).fillna("")

    found = 0

    for _, query in queries.iterrows():

        candidates = retrieve_candidates(
            query,
            catalog,
            limit=k,
        )

        expected = query["expected_code"]

        if expected in candidates["code"].values:
            found += 1

    recall = found / len(queries)

    print(f"Queries: {len(queries)}")
    print(f"Recall@{k}: {recall:.4f}")
    print(f"Found: {found}")
    print(f"Missing: {len(queries) - found}")


if __name__ == "__main__":
    evaluate(20)