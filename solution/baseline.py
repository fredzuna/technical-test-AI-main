"""Deliberately naive baseline. It exists to define the `make predict` contract
and to give you a floor on the scoreboard from minute one.

It does the dumbest defensible thing: token-overlap against ONE column of ONE of
the catalog files, no filtering, no calibration, review everything. It never opens
`manufacturers.csv`, `submodels.csv` or `version_years.csv`.

Whether that is enough - and what the unit of retrieval actually is - are
questions you should answer for yourself.

You are expected to replace it. Keep the input/output contract.
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path

import pandas as pd

TOKEN_RE = re.compile(r"[A-Z0-9.]+")
TOP_K = 3


def tokenize(text: object) -> set[str]:
    return set(TOKEN_RE.findall(str(text or "").upper()))


def build_index(catalog: pd.DataFrame) -> tuple[list[str], list[set[str]], Counter[str]]:
    """Inverted-frequency-free token sets over one catalog field.

    Note which field this reads, and note that it indexes rows as they appear in
    the file rather than deciding what a retrievable unit is.
    """
    codes = catalog["code"].astype(str).tolist()
    token_sets = [tokenize(text) for text in catalog["descveh"].tolist()]
    document_frequency: Counter[str] = Counter()
    for tokens in token_sets:
        document_frequency.update(tokens)
    return codes, token_sets, document_frequency


def rank(query: str, codes: list[str], token_sets: list[set[str]], document_frequency: Counter[str], n_docs: int) -> list[str]:
    query_tokens = tokenize(query)
    if not query_tokens:
        return codes[:TOP_K]

    scored: list[tuple[float, str]] = []
    for code, tokens in zip(codes, token_sets, strict=True):
        overlap = query_tokens & tokens
        if not overlap:
            continue
        # Rare shared tokens count for more than common ones.
        score = sum(1.0 / (1.0 + document_frequency[token] / n_docs) for token in overlap)
        scored.append((score, code))

    scored.sort(key=lambda pair: (-pair[0], pair[1]))
    top = [code for _, code in scored[:TOP_K]]
    return top or codes[:TOP_K]


def main() -> None:
    parser = argparse.ArgumentParser(description="Naive token-overlap baseline.")
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--versions", type=Path, required=True, help="data/versions.csv")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    catalog = pd.read_csv(args.versions, dtype=str).fillna("")
    queries = pd.read_csv(args.queries, dtype=str).fillna("")
    codes, token_sets, document_frequency = build_index(catalog)
    n_docs = max(1, len(codes))

    with args.out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["query_id", "top1_code", "top3_codes", "confidence", "decision"])
        for _, row in queries.iterrows():
            top = rank(row["description"], codes, token_sets, document_frequency, n_docs)
            # Constant confidence and blanket review: the floor policy, on purpose.
            writer.writerow([row["query_id"], top[0], "|".join(top), "0.50", "review"])

    print(f"wrote {args.out} ({len(queries)} rows)")


if __name__ == "__main__":
    main()
