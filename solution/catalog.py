from pathlib import Path

import pandas as pd


DATA_DIR = Path("data")


def load_catalog() -> pd.DataFrame:
    """
    Build a unified vehicle catalog from the source CSV files.

    Returns one row per vehicle version/code.
    """

    versions = pd.read_csv(
        DATA_DIR / "versions.csv",
        dtype=str,
    ).fillna("")

    manufacturers = pd.read_csv(
        DATA_DIR / "manufacturers.csv",
        dtype=str,
    ).fillna("")

    submodels = pd.read_csv(
        DATA_DIR / "submodels.csv",
        dtype=str,
    ).fillna("")

    version_years = pd.read_csv(
        DATA_DIR / "version_years.csv",
        dtype=str,
    ).fillna("")

    # ---------------------------------------------------------
    # 1. Add manufacturer name
    # versions.manufacturer_key -> manufacturers.code
    # ---------------------------------------------------------
    catalog = versions.merge(
        manufacturers[["code", "marca"]],
        left_on="manufacturer_key",
        right_on="code",
        how="left",
        suffixes=("", "_manufacturer"),
    )

    catalog = catalog.rename(
        columns={
            "marca": "manufacturer",
        }
    )

    catalog = catalog.drop(columns=["code_manufacturer"])

    # ---------------------------------------------------------
    # 2. Add submodel information
    # versions.submodel_key -> submodels.code
    # ---------------------------------------------------------
    catalog = catalog.merge(
        submodels[["code", "manufacturer_key", "submarca"]],
        left_on="submodel_key",
        right_on="code",
        how="left",
        suffixes=("", "_submodel"),
    )

    catalog = catalog.rename(
        columns={
            "submarca": "submodel",
            "manufacturer_key_submodel": "submodel_manufacturer_key",
        }
    )

    catalog = catalog.drop(columns=["code_submodel"])

    # ---------------------------------------------------------
    # 3. Aggregate available years
    # version_years.code -> versions.code
    # ---------------------------------------------------------
    years_by_code = (
        version_years
        .groupby("code")["modelo"]
        .apply(lambda values: sorted(set(values)))
        .to_dict()
    )

    catalog["years"] = catalog["code"].map(years_by_code)

    catalog["years"] = catalog["years"].apply(
        lambda value: value if isinstance(value, list) else []
    )

    # ---------------------------------------------------------
    # 4. Clean text fields
    # ---------------------------------------------------------
    text_columns = [
        "manufacturer",
        "submodel",
        "descveh",
        "tipveh",
        "cvesegm",
    ]

    for column in text_columns:
        catalog[column] = (
            catalog[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    return catalog

def validate_catalog() -> None:
    versions = pd.read_csv(
        DATA_DIR / "versions.csv",
        dtype=str,
    ).fillna("")

    submodels = pd.read_csv(
        DATA_DIR / "submodels.csv",
        dtype=str,
    ).fillna("")

    check = versions[
        ["code", "manufacturer_key", "submodel_key"]
    ].merge(
        submodels[
            ["code", "manufacturer_key"]
        ],
        left_on="submodel_key",
        right_on="code",
        how="left",
        suffixes=("_version", "_submodel"),
    )

    missing_submodels = (
        check["manufacturer_key_submodel"] == ""
    ).sum()

    inconsistent_manufacturers = (
        (check["manufacturer_key_submodel"] != "")
        & (
            check["manufacturer_key_version"]
            != check["manufacturer_key_submodel"]
        )
    ).sum()

    print("Missing submodel references:", missing_submodels)
    print(
        "Inconsistent manufacturer relationships:",
        inconsistent_manufacturers,
    )