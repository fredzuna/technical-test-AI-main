import pandas as pd

from catalog import load_catalog
from retrieval import retrieve_candidates


catalog = load_catalog()

queries = pd.read_csv(
    "data/queries_labeled.csv",
    dtype=str,
).fillna("")


for _, query in queries.head(10).iterrows():

    candidates = retrieve_candidates(
        query,
        catalog,
        limit=5,
    )

    print("\n" + "=" * 80)

    print(
        f"Query: {query['query_id']}"
    )

    print(
        f"Description: {query['description']}"
    )

    print(
        f"Expected: {query['expected_code']}"
    )

    print("\nCandidates:")

    print(
        candidates[
            [
                "code",
                "manufacturer",
                "submodel",
                "descveh",
                "retrieval_score",
            ]
        ].to_string(index=False)
    )

    expected = query["expected_code"]

    found = expected in candidates["code"].values

    print(
        f"\nExpected in top 5: {found}"
    )