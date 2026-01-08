"""Seed script for covered delivery areas."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sawt.db.connection import init_db, close_db, get_transaction


# Covered areas in Riyadh
COVERED_AREAS = [
    {
        "name_ar": "حي النرجس",
        "name_en": "Al Narjis",
        "city": "Riyadh",
        "aliases_ar": ["النرجس", "نرجس"],
    },
    {
        "name_ar": "حي الياسمين",
        "name_en": "Al Yasmin",
        "city": "Riyadh",
        "aliases_ar": ["الياسمين", "ياسمين"],
    },
    {
        "name_ar": "حي الملقا",
        "name_en": "Al Malqa",
        "city": "Riyadh",
        "aliases_ar": ["الملقا", "ملقا"],
    },
    {
        "name_ar": "حي الصحافة",
        "name_en": "Al Sahafa",
        "city": "Riyadh",
        "aliases_ar": ["الصحافة", "صحافة"],
    },
    {
        "name_ar": "حي العقيق",
        "name_en": "Al Aqiq",
        "city": "Riyadh",
        "aliases_ar": ["العقيق", "عقيق"],
    },
    {
        "name_ar": "حي الورود",
        "name_en": "Al Wurud",
        "city": "Riyadh",
        "aliases_ar": ["الورود", "ورود"],
    },
    {
        "name_ar": "حي الروضة",
        "name_en": "Al Rawdah",
        "city": "Riyadh",
        "aliases_ar": ["الروضة", "روضة"],
    },
    {
        "name_ar": "حي الربوة",
        "name_en": "Al Rabwah",
        "city": "Riyadh",
        "aliases_ar": ["الربوة", "ربوة"],
    },
    {
        "name_ar": "حي السليمانية",
        "name_en": "Al Sulaymaniyah",
        "city": "Riyadh",
        "aliases_ar": ["السليمانية", "سليمانية"],
    },
    {
        "name_ar": "حي الملك فهد",
        "name_en": "King Fahd District",
        "city": "Riyadh",
        "aliases_ar": ["الملك فهد", "ملك فهد"],
    },
    {
        "name_ar": "حي العليا",
        "name_en": "Al Olaya",
        "city": "Riyadh",
        "aliases_ar": ["العليا", "عليا"],
    },
    {
        "name_ar": "حي النخيل",
        "name_en": "Al Nakheel",
        "city": "Riyadh",
        "aliases_ar": ["النخيل", "نخيل"],
    },
    {
        "name_ar": "حي الغدير",
        "name_en": "Al Ghadir",
        "city": "Riyadh",
        "aliases_ar": ["الغدير", "غدير"],
    },
    {
        "name_ar": "حي القيروان",
        "name_en": "Al Qairawan",
        "city": "Riyadh",
        "aliases_ar": ["القيروان", "قيروان"],
    },
    {
        "name_ar": "حي الرمال",
        "name_en": "Al Rimal",
        "city": "Riyadh",
        "aliases_ar": ["الرمال", "رمال"],
    },
]

# Sample promo codes
PROMO_CODES = [
    {
        "code": "WELCOME10",
        "discount_type": "percentage",
        "discount_value": 10.00,
        "min_order_amount": 50.00,
        "max_discount": 30.00,
    },
    {
        "code": "FIRST20",
        "discount_type": "percentage",
        "discount_value": 20.00,
        "min_order_amount": 100.00,
        "max_discount": 50.00,
    },
    {
        "code": "FREE15",
        "discount_type": "fixed",
        "discount_value": 15.00,
        "min_order_amount": 75.00,
        "max_discount": None,
    },
]


async def seed_areas():
    """Seed the covered delivery areas and promo codes."""
    print("Seeding covered areas...")

    await init_db()

    try:
        async with get_transaction() as conn:
            # Clear existing data
            await conn.execute("DELETE FROM covered_areas")
            await conn.execute("DELETE FROM promo_codes")

            # Insert covered areas
            for area in COVERED_AREAS:
                await conn.execute(
                    """
                    INSERT INTO covered_areas (name_ar, name_en, city, aliases_ar)
                    VALUES ($1, $2, $3, $4)
                    """,
                    area["name_ar"],
                    area["name_en"],
                    area["city"],
                    area["aliases_ar"],
                )
                print(f"  Added area: {area['name_en']}")

            # Insert promo codes
            for promo in PROMO_CODES:
                await conn.execute(
                    """
                    INSERT INTO promo_codes (code, discount_type, discount_value, min_order_amount, max_discount)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    promo["code"],
                    promo["discount_type"],
                    promo["discount_value"],
                    promo["min_order_amount"],
                    promo["max_discount"],
                )
                print(f"  Added promo: {promo['code']}")

        print(f"\nSeeded {len(COVERED_AREAS)} areas and {len(PROMO_CODES)} promo codes.")

    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(seed_areas())
