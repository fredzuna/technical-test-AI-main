import re
import unicodedata
from vehicle_identity import extract_vehicle_identity
from text_utils import normalize_text
import pandas as pd

def tokens(value: str) -> set[str]:
    return set(normalize_text(value).split())


def token_similarity(a: str, b: str) -> float:
    a_tokens = tokens(a)
    b_tokens = tokens(b)

    if not a_tokens:
        return 0.0

    return len(a_tokens & b_tokens) / len(a_tokens)


def manufacturer_score(query, candidate) -> float:
    query_marca = normalize_text(query.get("marca", ""))

    if not query_marca:
        return 0.0

    candidate_marca = normalize_text(
        candidate.get("manufacturer", "")
    )

    return float(query_marca == candidate_marca)


def submodel_score(query, candidate) -> float:
    query_submodel = normalize_text(
        query.get("submarca", "")
    )

    if not query_submodel:
        return 0.0

    candidate_submodel = normalize_text(
        candidate.get("submodel", "")
    )

    return float(
        query_submodel == candidate_submodel
    )


def year_score(query, candidate) -> float:
    query_year = str(query.get("year", "")).strip()

    if not query_year:
        return 0.0

    years = candidate.get("years", [])

    return float(query_year in years)


def segment_score(query, candidate) -> float:
    query_segment = normalize_text(
        query.get("segment", "")
    )

    if not query_segment:
        return 0.0

    candidate_segment = normalize_text(
        candidate.get("cvesegm", "")
    )

    return float(
        query_segment == candidate_segment
    )


def type_score(query, candidate) -> float:
    query_type = normalize_text(
        query.get("tipveh", "")
    )

    if not query_type:
        return 0.0

    candidate_type = normalize_text(
        candidate.get("tipveh", "")
    )

    return float(
        query_type == candidate_type
    )


def rank_candidates(
    query: pd.Series,
    candidates: pd.DataFrame,
) -> pd.DataFrame:

    candidates = candidates.copy()

    description = query.get("description", "")

    candidates["description_score"] = candidates[
        "descveh"
    ].apply(
        lambda value: token_similarity(
            description,
            value,
        )
    )

    candidates["manufacturer_score"] = candidates.apply(
        lambda row: manufacturer_score(
            query,
            row,
        ),
        axis=1,
    )

    candidates["submodel_score"] = candidates.apply(
        lambda row: submodel_score(
            query,
            row,
        ),
        axis=1,
    )

    candidates["year_score"] = candidates.apply(
        lambda row: year_score(
            query,
            row,
        ),
        axis=1,
    )

    candidates["segment_score"] = candidates.apply(
        lambda row: segment_score(
            query,
            row,
        ),
        axis=1,
    )

    candidates["type_score"] = candidates.apply(
        lambda row: type_score(
            query,
            row,
        ),
        axis=1,
    )

    candidates["model_score"] = candidates.apply(
        lambda row: model_identity_score(
            query,
            row,
        ),
        axis=1,
    )    

    # ---------------------------------------------------------
    # Combined ranking score
    # ---------------------------------------------------------

    candidates["rank_score"] = (
        candidates["model_score"] * 0.30
        +candidates["description_score"] * 0.45
        + candidates["submodel_score"] * 0.25
        + candidates["manufacturer_score"] * 0.15
        + candidates["year_score"] * 0.10
        + candidates["segment_score"] * 0.025
        + candidates["type_score"] * 0.025
    )

    return candidates.sort_values(
        "rank_score",
        ascending=False,
    ).reset_index(drop=True)

def model_identity_score(query, candidate) -> float:
    query_identity = extract_vehicle_identity(
        query.get("description", "")
    )

    query_model = query_identity["model"]

    if not query_model:
        return 0.0

    candidate_text = normalize_text(
        f"{candidate.get('submodel', '')} "
        f"{candidate.get('descveh', '')}"
    )

    candidate_model = normalize_text(query_model)

    return float(
        candidate_model in candidate_text
    )