import re

from text_utils import normalize_text


def extract_vehicle_identity(description: str) -> dict:
    """
    Extract important vehicle identity signals from a description.
    """

    text = normalize_text(description)

    result = {
        "manufacturer": None,
        "model": None,
    }

    # ---------------------------------------------------------
    # Manufacturer
    # ---------------------------------------------------------

    manufacturers = [
        "FORD",
        "DODGE",
        "RAM",
        "TOYOTA",
        "CHEVROLET",
        "NISSAN",
        "HONDA",
        "HINO",
        "VOLVO",
        "FREIGHTLINER",
        "INTERNATIONAL",
        "MERCEDES BENZ",
        "MITSUBISHI",
        "ISUZU",
        "MAZDA",
        "VOLKSWAGEN",
        "AUDI",
        "BMW",
    ]

    for manufacturer in manufacturers:
        if manufacturer in text:
            result["manufacturer"] = manufacturer
            break

    # ---------------------------------------------------------
    # Common model patterns
    # ---------------------------------------------------------

    patterns = [
        # F-600, F 600, F600
        r"\bF[\s-]?\d{3}\b",

        # RAM 2500 / RAM 3500 / RAM 4000
        r"\bRAM[\s-]?\d{3,4}\b",

        # TACOMA
        r"\bTACOMA\b",

        # HINO 816
        r"\bHINO[\s-]?\d{3}\b",

        # CR-V
        r"\bCR[\s-]?V\b",

        # A3, A4, A6
        r"\bA[3-8]\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            result["model"] = (
                match.group(0)
                .replace("-", " ")
                .strip()
            )
            break

    return result