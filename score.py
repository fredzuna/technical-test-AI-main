"""Official scorer for the vehicle-matching work sample.

This is the exact script we run on your blind-set submission. Run it yourself
against the labeled dev set as often as you like:

    python score.py --predictions dev_predictions.csv --labels data/queries_labeled.csv

The headline number is MEAN UTILITY PER ROW. It is not accuracy. Read the
utility table below before you optimise anything.

    auto_accept + top1 correct        +1.00
    auto_accept + top1 wrong          -3.00
    review      + correct in top3     +0.15
    review      + correct not in top3 -0.05

A wrong auto-accept flows into a quote sent to a client, so it costs three
times what a correct one earns. Routing a row to a human is cheap but not
free. This is the real economics of the product, not an artificial puzzle.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Utility constants. These are the contract; do not change them locally or
# your self-scoring will diverge from ours.
# ---------------------------------------------------------------------------
U_AUTO_CORRECT = 1.00
U_AUTO_WRONG = -3.00
U_REVIEW_IN_TOP3 = 0.15
U_REVIEW_MISS = -0.05

VALID_DECISIONS = frozenset({"auto_accept", "review"})
TOP3_SEPARATOR = "|"

REQUIRED_PREDICTION_COLUMNS = frozenset({"query_id", "top1_code", "top3_codes", "confidence", "decision"})
REQUIRED_LABEL_COLUMNS = frozenset({"query_id", "expected_code"})


@dataclass
class Prediction:
    query_id: str
    top1_code: str
    top3_codes: tuple[str, ...]
    confidence: float
    decision: str


@dataclass
class Outcome:
    """Per-row scoring outcome, kept so the aggregate can be sliced."""

    query_id: str
    utility: float
    decision: str
    confidence: float
    top1_correct: bool
    in_top3: bool


@dataclass
class Report:
    outcomes: list[Outcome] = field(default_factory=list)

    @property
    def n(self) -> int:
        return len(self.outcomes)

    def _rate(self, predicate) -> float:  # noqa: ANN001 - local helper, callable over Outcome
        return sum(1 for o in self.outcomes if predicate(o)) / self.n if self.n else 0.0

    @property
    def mean_utility(self) -> float:
        return sum(o.utility for o in self.outcomes) / self.n if self.n else 0.0

    @property
    def top1_accuracy(self) -> float:
        return self._rate(lambda o: o.top1_correct)

    @property
    def top3_recall(self) -> float:
        return self._rate(lambda o: o.in_top3)

    @property
    def auto_accept_rate(self) -> float:
        return self._rate(lambda o: o.decision == "auto_accept")

    @property
    def auto_accept_precision(self) -> float:
        """Share of auto-accepted rows that were correct. The number that decides
        whether this system could be switched on in production."""
        accepted = [o for o in self.outcomes if o.decision == "auto_accept"]
        if not accepted:
            return 0.0
        return sum(1 for o in accepted if o.top1_correct) / len(accepted)

    @property
    def review_top3_recall(self) -> float:
        """Share of reviewed rows where the human would have seen the right answer."""
        reviewed = [o for o in self.outcomes if o.decision == "review"]
        if not reviewed:
            return 0.0
        return sum(1 for o in reviewed if o.in_top3) / len(reviewed)


def score_row(pred: Prediction, expected: str) -> Outcome:
    """Apply the utility table to a single row."""
    top1_correct = pred.top1_code == expected
    in_top3 = expected in pred.top3_codes

    if pred.decision == "auto_accept":
        utility = U_AUTO_CORRECT if top1_correct else U_AUTO_WRONG
    else:
        utility = U_REVIEW_IN_TOP3 if in_top3 else U_REVIEW_MISS

    return Outcome(
        query_id=pred.query_id,
        utility=utility,
        decision=pred.decision,
        confidence=pred.confidence,
        top1_correct=top1_correct,
        in_top3=in_top3,
    )


def _read_csv(path: Path, required: frozenset[str]) -> list[dict[str, str]]:
    if not path.exists():
        sys.exit(f"File not found: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        sys.exit(f"File is empty: {path}")
    missing = required - set(rows[0].keys())
    if missing:
        sys.exit(f"{path} is missing required columns: {sorted(missing)}")
    return rows


def load_predictions(path: Path) -> dict[str, Prediction]:
    predictions: dict[str, Prediction] = {}
    for line_no, row in enumerate(_read_csv(path, REQUIRED_PREDICTION_COLUMNS), start=2):
        query_id = (row["query_id"] or "").strip()
        if not query_id:
            sys.exit(f"{path}:{line_no} has an empty query_id")
        if query_id in predictions:
            sys.exit(f"{path}:{line_no} duplicates query_id {query_id}")

        decision = (row["decision"] or "").strip()
        if decision not in VALID_DECISIONS:
            sys.exit(f"{path}:{line_no} has decision={decision!r}, expected one of {sorted(VALID_DECISIONS)}")

        try:
            confidence = float(row["confidence"])
        except (TypeError, ValueError):
            sys.exit(f"{path}:{line_no} has a non-numeric confidence: {row['confidence']!r}")
        if not 0.0 <= confidence <= 1.0:
            sys.exit(f"{path}:{line_no} has confidence={confidence}, expected a value in [0, 1]")

        top3 = tuple(c.strip() for c in (row["top3_codes"] or "").split(TOP3_SEPARATOR) if c.strip())
        if len(top3) > 3:
            sys.exit(f"{path}:{line_no} lists {len(top3)} codes in top3_codes, maximum is 3")

        predictions[query_id] = Prediction(
            query_id=query_id,
            top1_code=(row["top1_code"] or "").strip(),
            top3_codes=top3,
            confidence=confidence,
            decision=decision,
        )
    return predictions


def load_labels(path: Path) -> dict[str, str]:
    return {row["query_id"].strip(): row["expected_code"].strip() for row in _read_csv(path, REQUIRED_LABEL_COLUMNS)}


def load_groups(path: Path, column: str) -> dict[str, str]:
    rows = _read_csv(path, frozenset({"query_id"}))
    if column not in rows[0]:
        sys.exit(f"--group-by column {column!r} not found in {path}. Available: {sorted(rows[0].keys())}")
    return {row["query_id"].strip(): (row[column] or "(blank)").strip() for row in rows}


def build_report(predictions: dict[str, Prediction], labels: dict[str, str]) -> Report:
    """Score every labeled row. A missing prediction is scored, not skipped.

    An absent row is treated as a review that failed to surface the answer
    (-0.05). Silently dropping unanswered rows would let a submission raise its
    mean by answering only the easy ones.
    """
    report = Report()
    for query_id, expected in labels.items():
        pred = predictions.get(query_id)
        if pred is None:
            report.outcomes.append(
                Outcome(query_id=query_id, utility=U_REVIEW_MISS, decision="review", confidence=0.0, top1_correct=False, in_top3=False)
            )
            continue
        report.outcomes.append(score_row(pred, expected))
    return report


def _format_report(title: str, report: Report) -> str:
    lines = [
        f"{title}  (n={report.n})",
        f"  mean utility per row     {report.mean_utility:+.4f}   <- headline",
        f"  top-1 accuracy           {report.top1_accuracy:6.1%}",
        f"  top-3 recall             {report.top3_recall:6.1%}",
        f"  auto-accept rate         {report.auto_accept_rate:6.1%}",
        f"  auto-accept precision    {report.auto_accept_precision:6.1%}   <- drives the -3.00 penalty",
        f"  top-3 recall on reviews  {report.review_top3_recall:6.1%}",
    ]
    return "\n".join(lines)


def _reference_baselines(report: Report) -> str:
    """Recompute the same rows under two trivial policies, for context.

    Neither is a strategy. They exist so you can see immediately whether your
    decision policy is adding value over doing nothing.
    """
    accept_all = sum(U_AUTO_CORRECT if o.top1_correct else U_AUTO_WRONG for o in report.outcomes)
    review_all = sum(U_REVIEW_IN_TOP3 if o.in_top3 else U_REVIEW_MISS for o in report.outcomes)
    n = report.n or 1
    return "\n".join(
        [
            "Reference policies, applied to your own candidate lists:",
            f"  if you auto-accepted every row   {accept_all / n:+.4f}",
            f"  if you reviewed every row        {review_all / n:+.4f}",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Score a vehicle-matching submission.")
    parser.add_argument("--predictions", type=Path, required=True, help="CSV produced by your solution")
    parser.add_argument("--labels", type=Path, required=True, help="CSV with query_id,expected_code")
    parser.add_argument("--group-by", type=str, default=None, help="Column in the labels file to break results down by")
    args = parser.parse_args()

    predictions = load_predictions(args.predictions)
    labels = load_labels(args.labels)

    unknown = set(predictions) - set(labels)
    if unknown:
        print(f"warning: {len(unknown)} predicted query_ids are not in the label file and were ignored\n")

    report = build_report(predictions, labels)
    print(_format_report("OVERALL", report))
    print()
    print(_reference_baselines(report))

    if args.group_by:
        groups = load_groups(args.labels, args.group_by)
        buckets: dict[str, Report] = defaultdict(Report)
        for outcome in report.outcomes:
            buckets[groups.get(outcome.query_id, "(unknown)")].outcomes.append(outcome)
        print()
        print(f"BREAKDOWN BY {args.group_by}")
        for name in sorted(buckets):
            print()
            print(_format_report(f"  {name}", buckets[name]))


if __name__ == "__main__":
    main()
