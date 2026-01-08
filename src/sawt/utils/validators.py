"""Validation utilities for Sawt."""

import re

from sawt.utils.numeral_converter import normalize_numerals


def validate_saudi_phone(phone: str) -> tuple[bool, str | None, str]:
    """
    Validate a Saudi Arabian phone number.

    Valid formats:
    - 05XXXXXXXX (10 digits starting with 05)
    - +966XXXXXXXXX (12 digits starting with +966)
    - 966XXXXXXXXX (12 digits starting with 966)

    Returns (is_valid, normalized_phone, error_message_ar).
    """
    # Normalize Arabic numerals
    phone = normalize_numerals(phone)

    # Remove spaces, dashes, parentheses
    phone = re.sub(r"[\s\-\(\)\.]", "", phone)

    # Check for international format
    if phone.startswith("+966"):
        phone = "0" + phone[4:]
    elif phone.startswith("966"):
        phone = "0" + phone[3:]

    # Validate Saudi mobile format (05XXXXXXXX)
    if not re.match(r"^05\d{8}$", phone):
        return False, None, "رقم الجوال غير صحيح. يجب أن يبدأ بـ 05 ويتكون من 10 أرقام"

    return True, phone, ""


def validate_customer_name(name: str) -> tuple[bool, str | None, str]:
    """
    Validate customer name.

    Requirements:
    - At least 2 characters
    - No special characters except spaces

    Returns (is_valid, cleaned_name, error_message_ar).
    """
    if not name or len(name.strip()) < 2:
        return False, None, "يرجى إدخال اسم صحيح (حرفين على الأقل)"

    # Clean the name
    cleaned = name.strip()

    # Remove extra spaces
    cleaned = " ".join(cleaned.split())

    # Check for invalid characters (allow Arabic, English, spaces)
    if not re.match(r"^[\u0600-\u06FF\u0750-\u077Fa-zA-Z\s]+$", cleaned):
        return False, None, "الاسم يجب أن يحتوي على حروف فقط"

    return True, cleaned, ""


def validate_address(
    area: str | None,
    street: str | None,
    building: str | None,
) -> tuple[bool, dict[str, str], list[str]]:
    """
    Validate delivery address components.

    Returns (is_complete, cleaned_parts, missing_fields_ar).
    """
    missing = []
    parts = {}

    if not area or len(area.strip()) < 2:
        missing.append("الحي/المنطقة")
    else:
        parts["area"] = area.strip()

    if not street or len(street.strip()) < 2:
        missing.append("الشارع")
    else:
        parts["street"] = street.strip()

    if not building or len(building.strip()) < 1:
        missing.append("رقم المبنى/الفيلا")
    else:
        parts["building"] = normalize_numerals(building.strip())

    return len(missing) == 0, parts, missing


def validate_quantity(quantity: int) -> tuple[bool, str]:
    """
    Validate item quantity.

    Returns (is_valid, error_message_ar).
    """
    if quantity < 1:
        return False, "الكمية يجب أن تكون 1 على الأقل"

    if quantity > 99:
        return False, "الحد الأقصى للكمية هو 99"

    return True, ""
