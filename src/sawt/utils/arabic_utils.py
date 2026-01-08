"""Arabic text processing utilities."""

import re
from typing import Any


def clean_arabic_text(text: str) -> str:
    """
    Clean and normalize Arabic text.

    - Removes extra whitespace
    - Normalizes Arabic characters (alef variations, etc.)
    - Removes diacritics (tashkeel)
    """
    if not text:
        return ""

    # Remove Arabic diacritics (tashkeel)
    diacritics = re.compile(r"[\u064B-\u065F\u0670]")
    text = diacritics.sub("", text)

    # Normalize alef variations to plain alef
    text = re.sub(r"[أإآا]", "ا", text)

    # Normalize teh marbuta to heh
    text = text.replace("ة", "ه")

    # Remove tatweel (kashida)
    text = text.replace("ـ", "")

    # Normalize whitespace
    text = " ".join(text.split())

    return text.strip()


def normalize_area_name(name: str) -> str:
    """
    Normalize an Arabic area/neighborhood name for matching.

    Handles common variations like:
    - "حي النرجس" vs "النرجس"
    - "الرياض" vs "رياض"
    """
    name = clean_arabic_text(name)

    # Remove common prefixes
    prefixes = ["حي ", "منطقة ", "شارع ", "طريق "]
    for prefix in prefixes:
        if name.startswith(prefix):
            name = name[len(prefix) :]

    return name.strip()


def format_price_ar(amount: float | int) -> str:
    """Format a price in Arabic style with SAR currency."""
    return f"{amount:.2f} ريال"


def format_order_summary_ar(
    items: list[dict[str, Any]],
    subtotal: float,
    delivery_fee: float,
    discount: float,
    total: float,
    is_pickup: bool = False,
) -> str:
    """
    Format an order summary in Arabic for display.

    Returns a formatted string suitable for chat display.
    """
    lines = ["📋 ملخص الطلب:", ""]

    for i, item in enumerate(items, 1):
        qty = item.get("quantity", 1)
        name = item.get("name_ar", item.get("item_name_ar", ""))
        price = item.get("total_price", item.get("line_total", 0))

        line = f"{i}. {qty}× {name} - {format_price_ar(price)}"

        # Add modifiers if present
        modifiers = item.get("modifiers", [])
        if modifiers:
            mod_names = [m.get("modifier_name_ar", m.get("name_ar", "")) for m in modifiers]
            if mod_names:
                line += f"\n   ({', '.join(mod_names)})"

        # Add special instructions
        instructions = item.get("special_instructions", "")
        if instructions:
            line += f"\n   ملاحظة: {instructions}"

        lines.append(line)

    lines.append("")
    lines.append(f"المجموع الفرعي: {format_price_ar(subtotal)}")

    if discount > 0:
        lines.append(f"الخصم: -{format_price_ar(discount)}")

    if not is_pickup and delivery_fee > 0:
        lines.append(f"رسوم التوصيل: {format_price_ar(delivery_fee)}")

    lines.append("")
    lines.append(f"الإجمالي (شامل الضريبة): {format_price_ar(total)}")

    return "\n".join(lines)


def format_cart_item_ar(item: dict[str, Any]) -> str:
    """Format a single cart item for display."""
    qty = item.get("quantity", 1)
    name = item.get("name_ar", "")
    price = item.get("unit_price", 0)

    text = f"{qty}× {name} ({format_price_ar(price)})"

    modifiers = item.get("modifiers", [])
    if modifiers:
        mod_names = [m.get("name_ar", "") for m in modifiers if m.get("name_ar")]
        if mod_names:
            text += f" + {', '.join(mod_names)}"

    return text


def is_affirmative_ar(text: str) -> bool:
    """Check if text is an affirmative response in Arabic."""
    affirmatives = [
        "نعم",
        "ايه",
        "اي",
        "صح",
        "تمام",
        "اوكي",
        "اوك",
        "ok",
        "yes",
        "يب",
        "اكيد",
        "طبعا",
        "بالتأكيد",
        "موافق",
    ]
    text_lower = text.strip().lower()
    return any(aff in text_lower for aff in affirmatives)


def is_negative_ar(text: str) -> bool:
    """Check if text is a negative response in Arabic."""
    negatives = [
        "لا",
        "لأ",
        "مو",
        "ما ابي",
        "ما اريد",
        "no",
        "كنسل",
        "الغي",
        "الغاء",
    ]
    text_lower = text.strip().lower()
    return any(neg in text_lower for neg in negatives)
