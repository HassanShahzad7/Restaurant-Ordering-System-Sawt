"""Checkout agent for finalizing orders."""

from sawt.agents.base_agent import BaseAgent, AgentResult
from sawt.llm.openrouter_client import OpenRouterClient
from sawt.state.session_state import SessionState
from sawt.state.machine import Trigger
from sawt.config import get_settings
from sawt.db.repositories.promo_repo import PromoRepository
from sawt.db.repositories.order_repo import OrderRepository
from sawt.llm.prompt_templates.checkout import get_checkout_prompt
from sawt.llm.prompt_templates.summarizer import get_confirmation_message
from sawt.utils.arabic_utils import format_order_summary_ar
from sawt.utils.validators import validate_saudi_phone, validate_customer_name
from sawt.utils.numeral_converter import normalize_numerals, extract_phone_number


class CheckoutAgent(BaseAgent):
    """Agent for checkout and order confirmation."""

    def __init__(self, llm_client: OpenRouterClient):
        super().__init__(llm_client)

    @property
    def name(self) -> str:
        return "checkout"

    @property
    def name_ar(self) -> str:
        return "مسؤول الدفع"

    def get_system_prompt(self, session: SessionState) -> str:
        """Get the checkout prompt with current context."""
        settings = get_settings()

        # Calculate totals
        subtotal = float(session.get_cart_subtotal())
        delivery_fee = float(settings.delivery_fee) if session.order_type == "delivery" else 0
        discount = 0.0
        promo_status = "لم يتم إدخال كود"

        if session.applied_promo_code:
            promo_status = f"كود: {session.applied_promo_code}"

        total = subtotal + delivery_fee - discount

        # Format order summary
        order_summary = format_order_summary_ar(
            items=[item.to_dict() for item in session.cart],
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            discount=discount,
            total=total,
            is_pickup=(session.order_type == "pickup"),
        )

        return get_checkout_prompt(
            order_summary,
            session.customer_name,
            session.customer_phone,
            promo_status,
        )

    async def process(
        self,
        user_message: str,
        session: SessionState,
    ) -> AgentResult:
        """Process checkout messages."""
        settings = get_settings()
        messages = self._build_messages(session, user_message)

        # Try to extract phone number from message
        extracted_phone = extract_phone_number(user_message)

        try:
            result = await self.llm.complete_json(messages, temperature=0.5)

            response_ar = result.get("response_ar", "")
            customer_update = result.get("customer_update", {})
            promo_code = result.get("promo_code")
            is_confirmed = result.get("is_confirmed", False)
            next_action = result.get("next_action", "continue")

            session_updates = {}

            # Update customer name
            if customer_update.get("name"):
                name = customer_update["name"]
                valid, cleaned_name, _ = validate_customer_name(name)
                if valid and cleaned_name:
                    session_updates["customer_name"] = cleaned_name

            # Update customer phone
            phone = customer_update.get("phone") or extracted_phone
            if phone:
                phone = normalize_numerals(phone)
                valid, normalized_phone, _ = validate_saudi_phone(phone)
                if valid and normalized_phone:
                    session_updates["customer_phone"] = normalized_phone

            # Apply promo code
            if promo_code and promo_code != session.applied_promo_code:
                subtotal = session.get_cart_subtotal()
                is_valid, discount, msg = await PromoRepository.validate_promo(
                    promo_code, subtotal
                )
                if is_valid:
                    session_updates["applied_promo_code"] = promo_code.upper()
                    response_ar = f"{msg}. {response_ar}" if response_ar else msg
                else:
                    response_ar = f"{msg}. {response_ar}" if response_ar else msg

            # Check if we can confirm the order
            final_name = session_updates.get("customer_name") or session.customer_name
            final_phone = session_updates.get("customer_phone") or session.customer_phone

            can_confirm = bool(
                session.cart
                and final_name
                and final_phone
                and (session.order_type == "pickup" or session.location.is_complete())
            )

            # Determine trigger
            if next_action == "order_confirmed" and is_confirmed and can_confirm:
                # Create the order
                order_result = await self._create_order(session, session_updates)

                if order_result.get("success"):
                    # Format confirmation message
                    subtotal = float(session.get_cart_subtotal())
                    delivery_fee = float(settings.delivery_fee) if session.order_type == "delivery" else 0

                    # Get discount if promo applied
                    discount = 0.0
                    promo_code_used = session_updates.get("applied_promo_code") or session.applied_promo_code
                    if promo_code_used:
                        _, disc, _ = await PromoRepository.validate_promo(promo_code_used, session.get_cart_subtotal())
                        discount = float(disc)

                    total = subtotal + delivery_fee - discount

                    order_summary = format_order_summary_ar(
                        items=[item.to_dict() for item in session.cart],
                        subtotal=subtotal,
                        delivery_fee=delivery_fee,
                        discount=discount,
                        total=total,
                        is_pickup=(session.order_type == "pickup"),
                    )

                    address = session.location.to_address_string() if session.location else "استلام من الفرع"

                    response_ar = get_confirmation_message(
                        order_number=order_result["order_number"],
                        order_summary=order_summary,
                        address=address,
                        customer_name=final_name,
                        customer_phone=final_phone,
                    )

                    trigger = Trigger.ORDER_CONFIRMED
                else:
                    response_ar = "حصل خطأ في إنشاء الطلب. يرجى المحاولة مرة ثانية."
                    trigger = None

            elif next_action == "modify_order":
                trigger = Trigger.MODIFY_ORDER
            elif next_action == "cancel":
                trigger = Trigger.CANCEL
            else:
                trigger = None  # Stay in checkout

            # If missing info, ask for it
            if not response_ar:
                missing = []
                if not final_name:
                    missing.append("اسمك")
                if not final_phone:
                    missing.append("رقم جوالك")
                if missing:
                    response_ar = f"عشان نأكد الطلب، أحتاج {' و'.join(missing)}."
                else:
                    response_ar = "تمام! تبي تأكد الطلب؟"

            return AgentResult(
                response_ar=response_ar,
                session_updates=session_updates,
                trigger=trigger,
                metadata={
                    "can_confirm": can_confirm,
                    "is_confirmed": is_confirmed,
                },
            )

        except Exception as e:
            return AgentResult(
                response_ar="أحتاج اسمك ورقم جوالك عشان أكمل الطلب.",
                metadata={"error": str(e)},
            )

    async def _create_order(
        self,
        session: SessionState,
        updates: dict,
    ) -> dict:
        """Create the order in the database."""
        from decimal import Decimal

        settings = get_settings()

        customer_name = updates.get("customer_name") or session.customer_name
        customer_phone = updates.get("customer_phone") or session.customer_phone

        if not customer_name or not customer_phone:
            return {"success": False, "error": "Missing customer info"}

        subtotal = session.get_cart_subtotal()
        delivery_fee = settings.delivery_fee if session.order_type == "delivery" else Decimal("0")

        # Calculate discount
        discount = Decimal("0")
        promo_code_id = None
        promo_code = updates.get("applied_promo_code") or session.applied_promo_code
        if promo_code:
            is_valid, disc, _ = await PromoRepository.validate_promo(promo_code, subtotal)
            if is_valid:
                discount = disc
                promo = await PromoRepository.get_promo_by_code(promo_code)
                if promo:
                    promo_code_id = promo["id"]
                    await PromoRepository.increment_usage(promo_code)

        total = subtotal + delivery_fee - discount

        # Prepare cart items for DB
        cart_items = []
        for item in session.cart:
            cart_items.append({
                "menu_item_id": item.menu_item_id,
                "item_name_ar": item.item_name_ar,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price),
                "total_price": float(item.total_price),
                "special_instructions": item.special_instructions,
                "modifiers": [
                    {
                        "modifier_id": m.modifier_id,
                        "modifier_name_ar": m.name_ar,
                        "price_adjustment": float(m.price_adjustment),
                    }
                    for m in item.modifiers
                ],
            })

        try:
            result = await OrderRepository.create_order(
                session_id=session.session_id,
                customer_name=customer_name,
                customer_phone=customer_phone,
                delivery_address=session.location.to_address_string() if session.location else None,
                delivery_area_id=session.location.area_id if session.location else None,
                order_type=session.order_type,
                subtotal=subtotal,
                delivery_fee=delivery_fee,
                discount_amount=discount,
                promo_code_id=promo_code_id,
                total=total,
                cart_items=cart_items,
            )

            return {
                "success": True,
                "order_id": result["order_id"],
                "order_number": result["order_number"],
            }

        except Exception as e:
            return {"success": False, "error": str(e)}
