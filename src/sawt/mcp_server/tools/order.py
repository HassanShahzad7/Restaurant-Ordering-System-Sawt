"""Order management tools for FastMCP."""

from decimal import Decimal

from fastmcp import FastMCP

from sawt.config import get_settings
from sawt.db.repositories.order_repo import OrderRepository
from sawt.db.repositories.session_repo import SessionRepository
from sawt.db.repositories.promo_repo import PromoRepository
from sawt.utils.arabic_utils import format_order_summary_ar, format_price_ar


def register_order_tools(mcp: FastMCP) -> None:
    """Register order management tools with the MCP server."""

    @mcp.tool()
    async def compute_totals(
        cart_items: list[dict],
        promo_code: str | None = None,
        order_type: str = "delivery",
    ) -> dict:
        """
        حساب إجمالي الطلب شامل التوصيل والخصم.

        Args:
            cart_items: قائمة عناصر السلة
            promo_code: كود الخصم (اختياري)
            order_type: نوع الطلب (delivery/pickup)

        Returns:
            dict with subtotal, delivery_fee, discount, total
        """
        settings = get_settings()

        # Calculate subtotal
        subtotal = Decimal("0")
        for item in cart_items:
            subtotal += Decimal(str(item.get("total_price", 0)))

        # Delivery fee (only for delivery orders)
        delivery_fee = Decimal("0")
        if order_type == "delivery":
            delivery_fee = settings.delivery_fee

        # Apply promo code
        discount = Decimal("0")
        promo_message = ""
        if promo_code:
            is_valid, disc_amount, msg = await PromoRepository.validate_promo(
                promo_code, subtotal
            )
            if is_valid:
                discount = disc_amount
                promo_message = msg
            else:
                promo_message = msg

        # Calculate total
        total = subtotal + delivery_fee - discount

        return {
            "subtotal": float(subtotal),
            "delivery_fee": float(delivery_fee),
            "discount": float(discount),
            "total": float(total),
            "promo_code": promo_code,
            "promo_message_ar": promo_message,
            "tax_included": settings.tax_included,
            "breakdown_ar": {
                "subtotal": format_price_ar(float(subtotal)),
                "delivery_fee": format_price_ar(float(delivery_fee)) if delivery_fee > 0 else None,
                "discount": f"-{format_price_ar(float(discount))}" if discount > 0 else None,
                "total": format_price_ar(float(total)),
            },
        }

    @mcp.tool()
    async def create_order(session_id: str) -> dict:
        """
        إنشاء الطلب النهائي وحفظه في قاعدة البيانات.

        Args:
            session_id: معرف الجلسة

        Returns:
            dict with order_id, order_number, confirmation message
        """
        # Get session data
        session = await SessionRepository.get_session(session_id)
        if not session:
            return {
                "success": False,
                "error_ar": "الجلسة غير موجودة",
            }

        # Validate required fields
        if not session.get("customer_name"):
            return {
                "success": False,
                "error_ar": "اسم العميل مطلوب",
            }

        if not session.get("customer_phone"):
            return {
                "success": False,
                "error_ar": "رقم الجوال مطلوب",
            }

        cart = session.get("cart", [])
        if not cart:
            return {
                "success": False,
                "error_ar": "السلة فارغة",
            }

        order_type = session.get("order_type", "delivery")

        # Compute totals
        totals = await compute_totals(
            cart,
            session.get("applied_promo_code"),
            order_type,
        )

        # Get promo code ID if applicable
        promo_code_id = None
        if session.get("applied_promo_code"):
            promo = await PromoRepository.get_promo_by_code(session["applied_promo_code"])
            if promo:
                promo_code_id = promo["id"]
                # Increment usage
                await PromoRepository.increment_usage(session["applied_promo_code"])

        # Create the order
        order_result = await OrderRepository.create_order(
            session_id=session_id,
            customer_name=session["customer_name"],
            customer_phone=session["customer_phone"],
            delivery_address=session.get("delivery_address"),
            delivery_area_id=session.get("delivery_area_id"),
            order_type=order_type,
            subtotal=Decimal(str(totals["subtotal"])),
            delivery_fee=Decimal(str(totals["delivery_fee"])),
            discount_amount=Decimal(str(totals["discount"])),
            promo_code_id=promo_code_id,
            total=Decimal(str(totals["total"])),
            cart_items=cart,
        )

        # Format confirmation message
        summary = format_order_summary_ar(
            items=cart,
            subtotal=totals["subtotal"],
            delivery_fee=totals["delivery_fee"],
            discount=totals["discount"],
            total=totals["total"],
            is_pickup=(order_type == "pickup"),
        )

        return {
            "success": True,
            "order_id": order_result["order_id"],
            "order_number": order_result["order_number"],
            "created_at": order_result["created_at"].isoformat(),
            "summary_ar": summary,
            "confirmation_ar": f"تم تأكيد طلبك رقم {order_result['order_number']} بنجاح! شكراً لك.",
        }

    @mcp.tool()
    async def get_order_status(order_id: int) -> dict:
        """
        الحصول على حالة الطلب.

        Args:
            order_id: رقم الطلب

        Returns:
            dict with order status and details
        """
        order = await OrderRepository.get_order_by_id(order_id)

        if not order:
            return {
                "found": False,
                "message_ar": "الطلب غير موجود",
            }

        status_ar = {
            "pending": "قيد الانتظار",
            "confirmed": "تم التأكيد",
            "preparing": "جاري التحضير",
            "ready": "جاهز",
            "out_for_delivery": "في الطريق",
            "delivered": "تم التسليم",
            "cancelled": "ملغي",
        }

        return {
            "found": True,
            "order_id": order["id"],
            "order_number": f"ORD-{order['id']:06d}",
            "status": order["status"],
            "status_ar": status_ar.get(order["status"], order["status"]),
            "customer_name": order["customer_name"],
            "total": float(order["total"]),
            "created_at": order["created_at"].isoformat(),
        }
