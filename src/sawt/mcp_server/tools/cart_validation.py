"""Cart validation tools for FastMCP."""

from decimal import Decimal
from typing import Any

from fastmcp import FastMCP

from sawt.db.repositories.menu_repo import MenuRepository
from sawt.utils.validators import validate_quantity


def register_cart_tools(mcp: FastMCP) -> None:
    """Register cart validation tools with the MCP server."""

    @mcp.tool()
    async def validate_cart_line(
        item_id: int,
        quantity: int,
        modifier_ids: list[int] | None = None,
    ) -> dict:
        """
        التحقق من صحة عنصر السلة قبل إضافته.

        Args:
            item_id: رقم الصنف
            quantity: الكمية
            modifier_ids: أرقام الإضافات المختارة (اختياري)

        Returns:
            dict with valid status, errors, and line_total
        """
        errors: list[str] = []
        modifier_ids = modifier_ids or []

        # Validate quantity
        qty_valid, qty_error = validate_quantity(quantity)
        if not qty_valid:
            errors.append(qty_error)

        # Get item details
        item = await MenuRepository.get_item_by_id(item_id)
        if not item:
            return {
                "valid": False,
                "errors": ["الصنف غير موجود"],
                "line_total": 0,
            }

        if not item["is_available"]:
            errors.append("الصنف غير متوفر حالياً")

        # Validate modifiers
        if modifier_ids:
            mod_valid, mod_errors = await MenuRepository.validate_modifiers_for_item(
                item_id, modifier_ids
            )
            if not mod_valid:
                errors.extend(mod_errors)

        # Calculate line total
        base_price = Decimal(str(item["price"]))
        modifier_total = Decimal("0")

        if modifier_ids:
            modifiers = await MenuRepository.get_modifiers_by_ids(modifier_ids)
            for mod in modifiers:
                modifier_total += Decimal(str(mod["price_adjustment"]))

        unit_price = base_price + modifier_total
        line_total = unit_price * quantity

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "item_id": item_id,
            "item_name_ar": item["name_ar"],
            "quantity": quantity,
            "base_price": float(base_price),
            "modifier_total": float(modifier_total),
            "unit_price": float(unit_price),
            "line_total": float(line_total),
        }

    @mcp.tool()
    async def build_cart_item(
        item_id: int,
        quantity: int,
        modifier_ids: list[int] | None = None,
        special_instructions: str | None = None,
    ) -> dict:
        """
        إنشاء عنصر سلة كامل مع جميع التفاصيل.

        Args:
            item_id: رقم الصنف
            quantity: الكمية
            modifier_ids: أرقام الإضافات المختارة (اختياري)
            special_instructions: ملاحظات خاصة (اختياري)

        Returns:
            dict with complete cart item or errors
        """
        modifier_ids = modifier_ids or []

        # Validate first
        validation = await validate_cart_line(item_id, quantity, modifier_ids)
        if not validation["valid"]:
            return {
                "success": False,
                "errors": validation["errors"],
            }

        # Get item details
        item = await MenuRepository.get_item_by_id(item_id)
        if not item:
            return {
                "success": False,
                "errors": ["الصنف غير موجود"],
            }

        # Get modifier details
        modifiers_info = []
        if modifier_ids:
            modifiers = await MenuRepository.get_modifiers_by_ids(modifier_ids)
            modifiers_info = [
                {
                    "modifier_id": m["id"],
                    "name_ar": m["name_ar"],
                    "price_adjustment": float(m["price_adjustment"]),
                }
                for m in modifiers
            ]

        cart_item = {
            "menu_item_id": item_id,
            "item_name_ar": item["name_ar"],
            "quantity": quantity,
            "unit_price": validation["unit_price"],
            "total_price": validation["line_total"],
            "modifiers": modifiers_info,
            "special_instructions": special_instructions,
        }

        return {
            "success": True,
            "cart_item": cart_item,
        }

    @mcp.tool()
    async def calculate_cart_subtotal(cart_items: list[dict]) -> dict:
        """
        حساب المجموع الفرعي للسلة.

        Args:
            cart_items: قائمة عناصر السلة

        Returns:
            dict with subtotal and item count
        """
        subtotal = Decimal("0")
        item_count = 0

        for item in cart_items:
            total_price = Decimal(str(item.get("total_price", 0)))
            subtotal += total_price
            item_count += item.get("quantity", 1)

        return {
            "subtotal": float(subtotal),
            "item_count": item_count,
            "line_count": len(cart_items),
        }
