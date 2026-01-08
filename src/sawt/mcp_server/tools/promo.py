"""Promo code tools for FastMCP."""

from decimal import Decimal

from fastmcp import FastMCP

from sawt.db.repositories.promo_repo import PromoRepository


def register_promo_tools(mcp: FastMCP) -> None:
    """Register promo code tools with the MCP server."""

    @mcp.tool()
    async def apply_promo_code(code: str, subtotal: float) -> dict:
        """
        التحقق من كود الخصم وتطبيقه.

        Args:
            code: كود الخصم
            subtotal: المجموع الفرعي للطلب

        Returns:
            dict with valid status, discount amount, and message
        """
        is_valid, discount, message = await PromoRepository.validate_promo(
            code, Decimal(str(subtotal))
        )

        return {
            "valid": is_valid,
            "code": code.upper(),
            "discount_amount": float(discount),
            "message_ar": message,
        }

    @mcp.tool()
    async def get_promo_details(code: str) -> dict:
        """
        الحصول على تفاصيل كود الخصم.

        Args:
            code: كود الخصم

        Returns:
            dict with promo details or not found
        """
        promo = await PromoRepository.get_promo_by_code(code)

        if not promo:
            return {
                "found": False,
                "message_ar": "كود الخصم غير موجود",
            }

        discount_desc = ""
        if promo["discount_type"] == "percentage":
            discount_desc = f"{promo['discount_value']}%"
            if promo["max_discount"]:
                discount_desc += f" (بحد أقصى {promo['max_discount']} ريال)"
        else:
            discount_desc = f"{promo['discount_value']} ريال"

        return {
            "found": True,
            "code": promo["code"],
            "discount_type": promo["discount_type"],
            "discount_value": float(promo["discount_value"]),
            "discount_description_ar": discount_desc,
            "min_order_amount": float(promo["min_order_amount"]),
            "is_active": promo["is_active"],
        }
