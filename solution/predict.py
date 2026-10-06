
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from catalog import load_catalog
from retrieval import retrieve_candidates
from hybrid_ranker import hybrid_rank
from confidence import calculate_confidence
from decision import make_decision


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate vehicle catalog predictions."
    )

    parser.add_argument(
        "--queries",
        required=True,
        help="Path to query CSV",
    )

    parser.add_argument(
        "--versions",
        required=True,
        help="Path to versions.csv",
    )

    parser.add_argument(
        "--out",
        required=True,
        help="Output predictions CSV",
    )

    parser.add_argument(
        "--threshold",
        type=float,
        default=0.80,
        help="Confidence threshold for auto_accept",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    queries_path = Path(args.queries)
    versions_path = Path(args.versions)
    output_path = Path(args.out)

    print(f"Loading queries: {queries_path}")
    queries = pd.read_csv(queries_path)

    print(f"Loading catalog: {versions_path}")
    catalog = load_catalog()

    print(f"Queries: {len(queries)}")
    print(f"Catalog rows: {len(catalog)}")

    predictions = []

    for index, query in queries.iterrows():
        query_id = query["query_id"]

        # ---------------------------------------------------------
        # 1. Retrieve candidates
        # ---------------------------------------------------------
        candidates = retrieve_candidates(
            query=query,
            catalog=catalog            
        )

        # ---------------------------------------------------------
        # 2. Rank candidates
        # ---------------------------------------------------------
        ranked = hybrid_rank(
            query=query,
            candidates=candidates,
        )

        if ranked.empty:
            raise RuntimeError(
                f"No candidates found for query {query_id}"
            )

        # ---------------------------------------------------------
        # 3. Get top 1 / top 3
        # ---------------------------------------------------------
        top1_code = str(ranked.iloc[0]["code"])

        top3_codes = [
            str(code)
            for code in ranked["code"].head(3).tolist()
        ]

        top3_codes_string = "|".join(top3_codes)

        # ---------------------------------------------------------
        # 4. Calculate confidence
        # ---------------------------------------------------------
        confidence = calculate_confidence(ranked)

        # ---------------------------------------------------------
        # 5. Make decision
        # ---------------------------------------------------------
        result = make_decision(
            ranked,
            args.threshold,
        )

        predictions.append(
            {
                "query_id": query_id,
                "top1_code": result["top1_code"],
                "top3_codes": result["top3_codes"],
                "confidence": round(float(result["confidence"]), 4),
                "decision": result["decision"],
            }
        )

        if (index + 1) % 25 == 0:
            print(
                f"Processed {index + 1}/{len(queries)} queries"
            )

    # -------------------------------------------------------------
    # 6. Write predictions
    # -------------------------------------------------------------
    result = pd.DataFrame(predictions)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.to_csv(
        output_path,
        index=False,
    )

    print()
    print("Prediction complete.")
    print(f"Output: {output_path}")
    print(f"Rows: {len(result)}")
    print()
    print("Decision counts:")
    print(result["decision"].value_counts())

    print()
    print("Sample:")
    print(result.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
