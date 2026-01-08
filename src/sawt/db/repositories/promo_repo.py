"""Promo code repository for database operations."""

from datetime import datetime
from decimal import Decimal
from typing import Any

import pytz

from sawt.config import get_settings
from sawt.db.connection import get_connection, get_transaction


class PromoRepository:
    """Repository for promo code operations."""

    @staticmethod
    async def get_promo_by_code(code: str) -> dict[str, Any] | None:
        """Get a promo code by its code string."""
        async with get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, code, discount_type, discount_value, min_order_amount,
                       max_discount, usage_limit, usage_count, valid_from,
                       valid_until, is_active
                FROM promo_codes
                WHERE UPPER(code) = UPPER($1)
                """,
                code,
            )
            return dict(row) if row else None

    @staticmethod
    async def validate_promo(
        code: str, subtotal: Decimal
    ) -> tuple[bool, Decimal, str]:
        """
        Validate a promo code and calculate discount.
        Returns (is_valid, discount_amount, message_ar).
        """
        promo = await PromoRepository.get_promo_by_code(code)

        if not promo:
            return False, Decimal("0"), "كود الخصم غير صحيح"

        if not promo["is_active"]:
            return False, Decimal("0"), "كود الخصم غير فعال"

        # Check usage limit
        if promo["usage_limit"] and promo["usage_count"] >= promo["usage_limit"]:
            return False, Decimal("0"), "تم استنفاد عدد استخدامات هذا الكود"

        # Check validity dates
        settings = get_settings()
        now = datetime.now(pytz.timezone(settings.timezone))

        if promo["valid_from"] and now < promo["valid_from"]:
            return False, Decimal("0"), "كود الخصم لم يبدأ بعد"

        if promo["valid_until"] and now > promo["valid_until"]:
            return False, Decimal("0"), "انتهت صلاحية كود الخصم"

        # Check minimum order amount
        if subtotal < promo["min_order_amount"]:
            return (
                False,
                Decimal("0"),
                f"الحد الأدنى للطلب {promo['min_order_amount']} ريال",
            )

        # Calculate discount
        if promo["discount_type"] == "percentage":
            discount = subtotal * promo["discount_value"] / 100
            if promo["max_discount"]:
                discount = min(discount, promo["max_discount"])
        else:  # fixed
            discount = promo["discount_value"]

        # Don't exceed subtotal
        discount = min(discount, subtotal)

        return True, discount, f"تم تطبيق خصم {discount} ريال"

    @staticmethod
    async def increment_usage(code: str) -> bool:
        """Increment the usage count for a promo code."""
        async with get_transaction() as conn:
            result = await conn.execute(
                """
                UPDATE promo_codes
                SET usage_count = usage_count + 1
                WHERE UPPER(code) = UPPER($1) AND is_active = true
                """,
                code,
            )
            return result == "UPDATE 1"

    @staticmethod
    async def get_active_promos() -> list[dict[str, Any]]:
        """Get all active promo codes."""
        settings = get_settings()
        now = datetime.now(pytz.timezone(settings.timezone))

        async with get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT id, code, discount_type, discount_value, min_order_amount,
                       max_discount, usage_limit, usage_count, valid_from, valid_until
                FROM promo_codes
                WHERE is_active = true
                  AND (valid_from IS NULL OR valid_from <= $1)
                  AND (valid_until IS NULL OR valid_until >= $1)
                  AND (usage_limit IS NULL OR usage_count < usage_limit)
                ORDER BY discount_value DESC
                """,
                now,
            )
            return [dict(row) for row in rows]
