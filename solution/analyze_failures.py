import pandas as pd

from catalog import load_catalog
from retrieval import retrieve_candidates
from ranking import rank_candidates


catalog = load_catalog()

queries = pd.read_csv(
    "data/queries_labeled.csv",
    dtype=str,
).fillna("")


failures = []

for _, query in queries.iterrows():

    candidates = retrieve_candidates(
        query,
        catalog,
        limit=20,
    )

    ranked = rank_candidates(
        query,
        candidates,
    )

    expected = query["expected_code"]

    if ranked.empty:
        continue

    top1 = ranked.iloc[0]

    expected_rows = ranked[
        ranked["code"] == expected
    ]

    if expected_rows.empty:
        expected_rank = None
        expected_score = None
    else:
        expected_rank = expected_rows.index[0] + 1
        expected_score = expected_rows.iloc[0]["rank_score"]

    if top1["code"] != expected:

        failures.append({
            "query_id": query["query_id"],
            "description": query["description"],
            "year": query["year"],
            "expected": expected,
            "predicted": top1["code"],
            "expected_rank": expected_rank,
            "predicted_score": round(
                top1["rank_score"], 3
            ),
            "expected_score": (
                round(expected_score, 3)
                if expected_score is not None
                else None
            ),
        })


failures_df = pd.DataFrame(failures)

print(f"Total failures: {len(failures_df)}")

print(
    "\nCorrect candidate NOT in top 20:"
)

print(
    failures_df["expected_rank"]
    .isna()
    .sum()
)

print(
    "\nCorrect candidate retrieved:"
)

print(
    failures_df["expected_rank"]
    .notna()
    .sum()
)

print("\nFirst 30 failures:")

print(
    failures_df
    .head(30)
    .to_string(index=False)
)