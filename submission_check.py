"""Validate predictions.csv before you submit it.

    python submission_check.py --predictions predictions.csv --queries data/queries_blind.csv

Run this. A submission that fails the format check cannot be scored, and we do
not repair submissions on your behalf.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from score import TOP3_SEPARATOR, VALID_DECISIONS, load_predictions


def _load_query_ids(path: Path) -> set[str]:
    if not path.exists():
        sys.exit(f"File not found: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or "query_id" not in rows[0]:
        sys.exit(f"{path} has no query_id column")
    return {row["query_id"].strip() for row in rows}


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a submission file.")
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True, help="The blind query file you were asked to predict")
    args = parser.parse_args()

    # load_predictions already exits on schema, decision, confidence and top3-length errors.
    predictions = load_predictions(args.predictions)
    expected_ids = _load_query_ids(args.queries)

    problems: list[str] = []

    missing = expected_ids - set(predictions)
    if missing:
        problems.append(f"{len(missing)} queries have no prediction, e.g. {sorted(missing)[:5]}")

    extra = set(predictions) - expected_ids
    if extra:
        problems.append(f"{len(extra)} predictions refer to unknown query_ids, e.g. {sorted(extra)[:5]}")

    empty_top1 = [p.query_id for p in predictions.values() if not p.top1_code]
    if empty_top1:
        problems.append(f"{len(empty_top1)} rows have an empty top1_code, e.g. {empty_top1[:5]}")

    top1_not_in_top3 = [p.query_id for p in predictions.values() if p.top1_code and p.top1_code not in p.top3_codes]
    if top1_not_in_top3:
        problems.append(
            f"{len(top1_not_in_top3)} rows have a top1_code absent from top3_codes "
            f"(top3_codes must be your ranked list, {TOP3_SEPARATOR}-separated, best first), e.g. {top1_not_in_top3[:5]}"
        )

    if problems:
        print("SUBMISSION INVALID")
        for problem in problems:
            print(f"  - {problem}")
        raise SystemExit(1)

    decisions = {d: sum(1 for p in predictions.values() if p.decision == d) for d in sorted(VALID_DECISIONS)}
    distinct_confidences = len({round(p.confidence, 6) for p in predictions.values()})

    print("SUBMISSION VALID")
    print(f"  rows                  {len(predictions)}")
    print(f"  decisions             {decisions}")
    print(f"  distinct confidences  {distinct_confidences}")
    if distinct_confidences <= 2:
        print("  note: your confidence column is nearly constant. That is a legitimate choice,")
        print("        but be aware it is also the signature of an uncalibrated system.")


if __name__ == "__main__":
    main()
