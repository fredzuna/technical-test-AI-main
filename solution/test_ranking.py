import pandas as pd

from catalog import load_catalog
from retrieval import retrieve_candidates
from ranking import rank_candidates


catalog = load_catalog()

queries = pd.read_csv(
    "data/queries_labeled.csv",
    dtype=str,
).fillna("")


for _, query in queries.head(10).iterrows():

    candidates = retrieve_candidates(
        query,
        catalog,
        limit=20,
    )

    ranked = rank_candidates(
        query,
        candidates,
    )

    print("\n" + "=" * 100)

    print("Query:", query["query_id"])
    print("Description:", query["description"])
    print("Expected:", query["expected_code"])

    print("\nTop candidates:")

    print(
        ranked[
            [
                "code",
                "manufacturer",
                "submodel",
                "description_score",
                "manufacturer_score",
                "submodel_score",
                "year_score",
                "segment_score",
                "type_score",
                "rank_score",
            ]
        ]
        .head(5)
        .to_string(index=False)
    )

    print(
        "\nPrediction:",
        ranked.iloc[0]["code"],
    )

    print(
        "Correct:",
        ranked.iloc[0]["code"]
        == query["expected_code"],
    )