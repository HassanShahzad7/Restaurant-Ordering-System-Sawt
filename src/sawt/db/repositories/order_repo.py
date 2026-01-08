"""Order repository for database operations."""

from datetime import datetime
from decimal import Decimal
from typing import Any

import pytz

from sawt.config import get_settings
from sawt.db.connection import get_connection, get_transaction


class OrderRepository:
    """Repository for order operations."""

    @staticmethod
    async def create_order(
        session_id: str,
        customer_name: str,
        customer_phone: str,
        delivery_address: str | None,
        delivery_area_id: int | None,
        order_type: str,
        subtotal: Decimal,
        delivery_fee: Decimal,
        discount_amount: Decimal,
        promo_code_id: int | None,
        total: Decimal,
        cart_items: list[dict[str, Any]],
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Create a new order with all items."""
        settings = get_settings()
        now = datetime.now(pytz.timezone(settings.timezone))

        async with get_transaction() as conn:
            # Create the order
            order_row = await conn.fetchrow(
                """
                INSERT INTO orders (
                    session_id, customer_name, customer_phone, delivery_address,
                    delivery_area_id, order_type, subtotal, delivery_fee,
                    discount_amount, promo_code_id, total, status, notes,
                    created_at, updated_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, 'confirmed', $12, $13, $13)
                RETURNING id, created_at
                """,
                session_id,
                customer_name,
                customer_phone,
                delivery_address,
                delivery_area_id,
                order_type,
                subtotal,
                delivery_fee,
                discount_amount,
                promo_code_id,
                total,
                notes,
                now,
            )

            order_id = order_row["id"]

            # Create order items
            for item in cart_items:
                order_item_row = await conn.fetchrow(
                    """
                    INSERT INTO order_items (
                        order_id, menu_item_id, item_name_ar, quantity,
                        unit_price, total_price, special_instructions
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING id
                    """,
                    order_id,
                    item["menu_item_id"],
                    item["item_name_ar"],
                    item["quantity"],
                    item["unit_price"],
                    item["total_price"],
                    item.get("special_instructions"),
                )

                order_item_id = order_item_row["id"]

                # Create order item modifiers
                for modifier in item.get("modifiers", []):
                    await conn.execute(
                        """
                        INSERT INTO order_item_modifiers (
                            order_item_id, modifier_id, modifier_name_ar, price_adjustment
                        )
                        VALUES ($1, $2, $3, $4)
                        """,
                        order_item_id,
                        modifier["modifier_id"],
                        modifier["modifier_name_ar"],
                        modifier["price_adjustment"],
                    )

            return {
                "order_id": order_id,
                "created_at": order_row["created_at"],
                "order_number": f"ORD-{order_id:06d}",
            }

    @staticmethod
    async def get_order_by_id(order_id: int) -> dict[str, Any] | None:
        """Get an order by ID with all its items."""
        async with get_connection() as conn:
            order = await conn.fetchrow(
                """
                SELECT o.*, ca.name_ar as area_name_ar
                FROM orders o
                LEFT JOIN covered_areas ca ON o.delivery_area_id = ca.id
                WHERE o.id = $1
                """,
                order_id,
            )
            if not order:
                return None

            result = dict(order)

            # Get order items
            items = await conn.fetch(
                """
                SELECT oi.*, mi.name_ar as menu_item_name_ar
                FROM order_items oi
                LEFT JOIN menu_items mi ON oi.menu_item_id = mi.id
                WHERE oi.order_id = $1
                """,
                order_id,
            )

            result["items"] = []
            for item in items:
                item_dict = dict(item)
                # Get modifiers for this item
                modifiers = await conn.fetch(
                    """
                    SELECT * FROM order_item_modifiers
                    WHERE order_item_id = $1
                    """,
                    item["id"],
                )
                item_dict["modifiers"] = [dict(m) for m in modifiers]
                result["items"].append(item_dict)

            return result

    @staticmethod
    async def get_orders_by_session(session_id: str) -> list[dict[str, Any]]:
        """Get all orders for a session."""
        async with get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT id, customer_name, customer_phone, order_type,
                       total, status, created_at
                FROM orders
                WHERE session_id = $1
                ORDER BY created_at DESC
                """,
                session_id,
            )
            return [dict(row) for row in rows]

    @staticmethod
    async def get_orders_by_phone(phone: str) -> list[dict[str, Any]]:
        """Get all orders for a phone number."""
        async with get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT id, customer_name, customer_phone, order_type,
                       total, status, created_at
                FROM orders
                WHERE customer_phone = $1
                ORDER BY created_at DESC
                LIMIT 10
                """,
                phone,
            )
            return [dict(row) for row in rows]

    @staticmethod
    async def update_order_status(order_id: int, status: str) -> bool:
        """Update order status."""
        settings = get_settings()
        now = datetime.now(pytz.timezone(settings.timezone))

        async with get_transaction() as conn:
            result = await conn.execute(
                """
                UPDATE orders
                SET status = $2, updated_at = $3
                WHERE id = $1
                """,
                order_id,
                status,
                now,
            )
            return result == "UPDATE 1"

    @staticmethod
    async def get_recent_orders(limit: int = 20) -> list[dict[str, Any]]:
        """Get recent orders."""
        async with get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT o.id, o.customer_name, o.customer_phone, o.order_type,
                       o.total, o.status, o.created_at, ca.name_ar as area_name_ar
                FROM orders o
                LEFT JOIN covered_areas ca ON o.delivery_area_id = ca.id
                ORDER BY o.created_at DESC
                LIMIT $1
                """,
                limit,
            )
            return [dict(row) for row in rows]
