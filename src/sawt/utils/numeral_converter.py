"""Arabic numeral conversion utilities."""

# Arabic-Indic numerals to Western Arabic numerals mapping
ARABIC_INDIC_TO_WESTERN = {
    "٠": "0",
    "١": "1",
    "٢": "2",
    "٣": "3",
    "٤": "4",
    "٥": "5",
    "٦": "6",
    "٧": "7",
    "٨": "8",
    "٩": "9",
}

# Extended Arabic-Indic numerals (Persian/Urdu style)
EXTENDED_ARABIC_TO_WESTERN = {
    "۰": "0",
    "۱": "1",
    "۲": "2",
    "۳": "3",
    "۴": "4",
    "۵": "5",
    "۶": "6",
    "۷": "7",
    "۸": "8",
    "۹": "9",
}


def normalize_numerals(text: str) -> str:
    """
    Convert Arabic-Indic numerals (٠-٩) and extended Arabic numerals (۰-۹)
    to Western Arabic numerals (0-9).

    Args:
        text: Input text that may contain Arabic numerals.

    Returns:
        Text with all Arabic numerals converted to Western digits.
    """
    result = text

    # Convert Arabic-Indic numerals
    for ar, en in ARABIC_INDIC_TO_WESTERN.items():
        result = result.replace(ar, en)

    # Convert extended Arabic numerals
    for ar, en in EXTENDED_ARABIC_TO_WESTERN.items():
        result = result.replace(ar, en)

    return result


def extract_phone_number(text: str) -> str | None:
    """
    Extract and normalize a Saudi phone number from text.

    Handles formats like:
    - 0551234567
    - 05٥١٢٣٤٥٦٧
    - +966551234567
    - 966551234567

    Returns normalized phone number or None if not found.
    """
    import re

    # Normalize numerals first
    normalized = normalize_numerals(text)

    # Remove common separators
    normalized = normalized.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

    # Try to extract phone number patterns
    patterns = [
        r"(\+?966[0-9]{9})",  # International format
        r"(0[0-9]{9})",  # Local format
    ]

    for pattern in patterns:
        match = re.search(pattern, normalized)
        if match:
            phone = match.group(1)
            # Normalize to local format (05XXXXXXXX)
            if phone.startswith("+966"):
                phone = "0" + phone[4:]
            elif phone.startswith("966"):
                phone = "0" + phone[3:]
            return phone

    return None


def extract_quantity(text: str) -> int | None:
    """
    Extract a quantity number from text.

    Handles Arabic and Western numerals.
    Returns the first number found or None.
    """
    import re

    normalized = normalize_numerals(text)
    match = re.search(r"\d+", normalized)
    if match:
        return int(match.group())
    return None
