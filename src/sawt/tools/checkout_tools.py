"""Checkout tools for the ordering agent."""

import asyncio
import uuid
from datetime import datetime
from decimal import Decimal

import psycopg2
from langchain_core.tools import tool

from sawt.config import get_settings
from sawt.logging_config import log_tool_call, log_tool_result
from sawt.tools.order_tools import get_session_order, clear_session_order


# Store confirmed orders (backup in memory)
_confirmed_orders: dict[str, dict] = {}


def save_order_to_database_sync(
    order_id: str,
    session_id: str,
    customer_name: str,
    customer_phone: str,
    district: str,
    order_type: str,
    order_items: list[dict],
    subtotal: float,
    delivery_fee: float,
    discount: float,
    total: float,
    notes: str = ""
) -> bool:
    """Save the order to the PostgreSQL database using synchronous psycopg2."""
    try:
        settings = get_settings()

        # Connect to database
        conn = psycopg2.connect(settings.database_url)
        cursor = conn.cursor()

        try:
            # Insert the order
            cursor.execute(
                """
                INSERT INTO orders (
                    session_id, customer_name, customer_phone,
                    delivery_address, order_type, subtotal,
                    delivery_fee, discount_amount, total, status, notes
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'confirmed', %s)
                RETURNING id
                """,
                (
                    session_id,
                    customer_name,
                    customer_phone,
                    district,
                    order_type,
                    Decimal(str(subtotal)),
                    Decimal(str(delivery_fee)),
                    Decimal(str(discount)),
                    Decimal(str(total)),
                    notes
                )
            )
            order_db_id = cursor.fetchone()[0]

            # Insert order items
            for item in order_items:
                cursor.execute(
                    """
                    INSERT INTO order_items (
                        order_id, menu_item_id, item_name_ar,
                        quantity, unit_price, total_price, special_instructions
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        order_db_id,
                        int(item["item_id"]),
                        item["name_ar"],
                        item["quantity"],
                        Decimal(str(item["price"])),
                        Decimal(str(item["line_total"])),
                        item.get("notes", "")
                    )
                )

            conn.commit()
            return True

        except Exception as e:
            conn.rollback()
            print(f"Error in database transaction: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        print(f"Error connecting to database: {e}")
        return False


async def save_order_to_database(
    order_id: str,
    session_id: str,
    customer_name: str,
    customer_phone: str,
    district: str,
    order_type: str,
    order_items: list[dict],
    subtotal: float,
    delivery_fee: float,
    discount: float,
    total: float,
    notes: str = ""
) -> bool:
    """Save the order to the PostgreSQL database."""
    try:
        from sawt.db.connection import DatabasePool

        async with DatabasePool.transaction() as conn:
            # Insert the order
            order_db_id = await conn.fetchval(
                """
                INSERT INTO orders (
                    session_id, customer_name, customer_phone,
                    delivery_address, order_type, subtotal,
                    delivery_fee, discount_amount, total, status, notes
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, 'confirmed', $10)
                RETURNING id
                """,
                session_id,
                customer_name,
                customer_phone,
                district,
                order_type,
                subtotal,
                delivery_fee,
                discount,
                total,
                notes
            )

            # Insert order items
            for item in order_items:
                await conn.execute(
                    """
                    INSERT INTO order_items (
                        order_id, menu_item_id, item_name_ar,
                        quantity, unit_price, total_price, special_instructions
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    order_db_id,
                    int(item["item_id"]),
                    item["name_ar"],
                    item["quantity"],
                    item["price"],
                    item["line_total"],
                    item.get("notes", "")
                )

        return True
    except Exception as e:
        print(f"Error saving order to database: {e}")
        return False


@tool
def calculate_total(session_id: str = "default", delivery_fee: float = 0.0, promo_code: str | None = None) -> dict:
    """
    Calculate the final order total including delivery and any discounts.

    Args:
        session_id: Session identifier
        delivery_fee: Delivery fee in SAR
        promo_code: Optional promo code to apply

    Returns:
        Dictionary with:
        - subtotal: Items subtotal
        - delivery_fee: Delivery fee
        - discount: Any discount applied
        - total: Final total
        - breakdown_ar: Arabic breakdown of charges
    """
    log_tool_call("calculate_total", {"session_id": session_id, "delivery_fee": delivery_fee, "promo_code": promo_code})

    order = get_session_order(session_id)

    if not order:
        result = {
            "success": False,
            "message_ar": "السلة فارغة"
        }
        log_tool_result("calculate_total", result)
        return result

    subtotal = sum(item["line_total"] for item in order)
    discount = 0.0

    # Apply promo code
    promo_message = ""
    if promo_code:
        promo_code_upper = promo_code.upper()
        # Simple promo codes
        if promo_code_upper == "WELCOME10":
            discount = subtotal * 0.10
            if discount > 30:
                discount = 30
            promo_message = f"خصم 10% (حد أقصى 30 ريال): -{discount} ريال"
        elif promo_code_upper == "FIRST20":
            if subtotal >= 100:
                discount = subtotal * 0.20
                if discount > 50:
                    discount = 50
                promo_message = f"خصم 20% (حد أقصى 50 ريال): -{discount} ريال"
            else:
                promo_message = "الحد الأدنى للطلب 100 ريال لاستخدام هذا الكود"
        elif promo_code_upper == "FREE15":
            if subtotal >= 75:
                discount = 15.0
                promo_message = "خصم 15 ريال"
            else:
                promo_message = "الحد الأدنى للطلب 75 ريال لاستخدام هذا الكود"
        else:
            promo_message = "كود الخصم غير صحيح"

    total = subtotal + delivery_fee - discount

    # Build Arabic breakdown
    breakdown_lines = [
        f"المجموع الفرعي: {subtotal} ريال",
    ]
    if delivery_fee > 0:
        breakdown_lines.append(f"رسوم التوصيل: {delivery_fee} ريال")
    if discount > 0:
        breakdown_lines.append(f"الخصم: -{discount} ريال")
    breakdown_lines.append(f"الإجمالي: {total} ريال")
    if promo_message:
        breakdown_lines.append(f"\n{promo_message}")

    breakdown_ar = "\n".join(breakdown_lines)

    result = {
        "success": True,
        "subtotal": subtotal,
        "delivery_fee": delivery_fee,
        "discount": discount,
        "total": total,
        "breakdown_ar": breakdown_ar,
        "promo_applied": discount > 0
    }

    log_tool_result("calculate_total", {"total": total, "discount": discount})
    return result


@tool
def confirm_order(
    session_id: str = "default",
    customer_name: str = "",
    customer_phone: str = "",
    district: str = "",
    delivery_fee: float = 0.0,
    discount: float = 0.0,
    order_type: str = "delivery",
    notes: str = ""
) -> dict:
    """
    Confirm and finalize the order.

    Args:
        session_id: Session identifier
        customer_name: Customer name
        customer_phone: Customer phone number
        district: Delivery district
        delivery_fee: Delivery fee
        discount: Discount amount from promo code
        order_type: "delivery" or "pickup"
        notes: Order notes

    Returns:
        Dictionary with:
        - success: bool
        - order_id: Unique order ID
        - confirmation_ar: Arabic confirmation message
    """
    log_tool_call("confirm_order", {
        "session_id": session_id,
        "customer_name": customer_name,
        "district": district,
        "order_type": order_type,
        "discount": discount
    })

    order_items = get_session_order(session_id)

    if not order_items:
        result = {
            "success": False,
            "message_ar": "السلة فارغة"
        }
        log_tool_result("confirm_order", result)
        return result

    if not customer_name:
        result = {
            "success": False,
            "message_ar": "يرجى إدخال الاسم"
        }
        log_tool_result("confirm_order", result)
        return result

    if not customer_phone:
        result = {
            "success": False,
            "message_ar": "يرجى إدخال رقم الجوال"
        }
        log_tool_result("confirm_order", result)
        return result

    # Calculate totals
    subtotal = sum(item["line_total"] for item in order_items)
    actual_delivery_fee = delivery_fee if order_type == "delivery" else 0
    total = subtotal + actual_delivery_fee - discount

    # Generate order ID
    order_id = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"

    # Create order record
    order_record = {
        "order_id": order_id,
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "district": district,
        "order_type": order_type,
        "items": order_items,
        "subtotal": subtotal,
        "delivery_fee": actual_delivery_fee,
        "discount": discount,
        "total": total,
        "notes": notes,
        "status": "confirmed",
        "created_at": datetime.now().isoformat()
    }

    # Store order in memory (backup)
    _confirmed_orders[order_id] = order_record

    # Save to database synchronously (avoiding event loop conflicts)
    db_saved = False
    try:
        db_saved = save_order_to_database_sync(
            order_id=order_id,
            session_id=session_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            district=district,
            order_type=order_type,
            order_items=order_items,
            subtotal=subtotal,
            delivery_fee=actual_delivery_fee,
            discount=discount,
            total=total,
            notes=notes
        )
        if db_saved:
            print(f"Order {order_id} saved to database successfully")
        else:
            print(f"Order {order_id} NOT saved to database - stored in memory only")
    except Exception as e:
        print(f"Failed to save order to database: {e}")

    # Clear session cart
    clear_session_order(session_id)

    # Build confirmation message
    items_summary = "\n".join([
        f"  • {item['quantity']}× {item['name_ar']} = {item['line_total']} ريال"
        for item in order_items
    ])

    if order_type == "delivery":
        location_text = f"📍 التوصيل إلى: {district}"
        fee_text = f"🚗 رسوم التوصيل: {actual_delivery_fee} ريال"
    else:
        location_text = "📍 استلام من الفرع"
        fee_text = ""

    discount_text = f"🎁 الخصم: -{discount} ريال" if discount > 0 else ""

    confirmation_ar = f"""✅ تم تأكيد طلبك!

🔢 رقم الطلب: {order_id}

📋 الطلب:
{items_summary}

💰 المجموع: {subtotal} ريال
{fee_text}
{discount_text}
💵 الإجمالي: {total} ريال

{location_text}
👤 الاسم: {customer_name}
📱 الجوال: {customer_phone}

💳 الدفع عند الاستلام

شكراً لك! 🙏"""

    result = {
        "success": True,
        "order_id": order_id,
        "total": total,
        "confirmation_ar": confirmation_ar
    }

    log_tool_result("confirm_order", {"success": True, "order_id": order_id, "saved_to_db": db_saved if 'db_saved' in dir() else False})
    return result


def get_confirmed_order(order_id: str) -> dict | None:
    """Get a confirmed order by ID."""
    return _confirmed_orders.get(order_id)
