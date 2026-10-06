from catalog import load_catalog


catalog = load_catalog()

print("Catalog rows:", len(catalog))
print("Catalog columns:")
print(catalog.columns.tolist())

print("\nFirst 5 rows:")
print(
    catalog[
        [
            "code",
            "manufacturer",
            "submodel",
            "descveh",
            "tipveh",
            "cvesegm",
            "years",
        ]
    ]
    .head()
    .to_string(index=False)
)

print("\nMissing manufacturer:")
print((catalog["manufacturer"] == "").sum())

print("Missing submodel:")
print((catalog["submodel"] == "").sum())

print("Missing years:")
print((catalog["years"].apply(len) == 0).sum())

print("\nUnique vehicle codes:")
print(catalog["code"].nunique())