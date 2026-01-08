"""Order agent for managing the menu and cart."""

from decimal import Decimal

from sawt.agents.base_agent import BaseAgent, AgentResult
from sawt.llm.openrouter_client import OpenRouterClient
from sawt.state.session_state import SessionState, CartItem, CartItemModifier
from sawt.state.machine import Trigger
from sawt.db.repositories.menu_repo import MenuRepository
from sawt.vector.pinecone_client import search_menu_items
from sawt.llm.prompt_templates.order import get_order_prompt
from sawt.utils.arabic_utils import format_cart_item_ar


class OrderAgent(BaseAgent):
    """Agent for managing menu search and cart operations."""

    def __init__(self, llm_client: OpenRouterClient):
        super().__init__(llm_client)

    @property
    def name(self) -> str:
        return "order"

    @property
    def name_ar(self) -> str:
        return "آخذ الطلبات"

    def get_system_prompt(self, session: SessionState) -> str:
        """Get the order prompt with current context."""
        # Format cart summary
        if session.cart:
            cart_lines = []
            for i, item in enumerate(session.cart, 1):
                cart_lines.append(f"{i}. {format_cart_item_ar(item.to_dict())}")
            cart_summary = "\n".join(cart_lines)
        else:
            cart_summary = "السلة فارغة"

        subtotal = float(session.get_cart_subtotal())

        # Get categories (will be fetched asynchronously in process)
        categories: list[str] = []

        return get_order_prompt(cart_summary, subtotal, categories)

    async def process(
        self,
        user_message: str,
        session: SessionState,
    ) -> AgentResult:
        """Process order-related messages."""
        # Get categories for context
        categories = await MenuRepository.get_all_categories()

        # Search for items if the message seems like a search query
        search_results = ""
        items_found = []

        # Try to search for items
        try:
            items_found = await search_menu_items(user_message, top_k=5)
            if items_found:
                search_lines = []
                for item in items_found:
                    search_lines.append(
                        f"- [{item['id']}] {item['name_ar']} - {item['price']} ريال"
                    )
                search_results = "\n".join(search_lines)
        except Exception:
            # Fallback to DB search
            items_found = await MenuRepository.search_items(user_message, limit=5)
            if items_found:
                search_lines = []
                for item in items_found:
                    search_lines.append(
                        f"- [{item['id']}] {item['name_ar']} - {item['price']} ريال"
                    )
                search_results = "\n".join(search_lines)

        # Build prompt with search results
        cart_summary = ""
        if session.cart:
            cart_lines = []
            for i, item in enumerate(session.cart, 1):
                cart_lines.append(f"{i}. {format_cart_item_ar(item.to_dict())}")
            cart_summary = "\n".join(cart_lines)

        prompt = get_order_prompt(
            cart_summary or "السلة فارغة",
            float(session.get_cart_subtotal()),
            categories,
            search_results,
        )

        messages = [{"role": "system", "content": prompt}]

        if session.conversation_summary_ar:
            messages.append({
                "role": "system",
                "content": f"ملخص المحادثة:\n{session.conversation_summary_ar}",
            })

        # Add recent history
        for msg in session.conversation_history[-4:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": user_message})

        try:
            result = await self.llm.complete_json(messages, temperature=0.6)

            response_ar = result.get("response_ar", "وش تبي تطلب؟")
            cart_action = result.get("cart_action", {})
            next_action = result.get("next_action", "continue_ordering")

            # Handle cart actions
            session_updates = {}
            new_cart = list(session.cart)

            if cart_action.get("type") == "add" and cart_action.get("item_id"):
                item_id = cart_action["item_id"]
                quantity = cart_action.get("quantity", 1)
                modifier_ids = cart_action.get("modifier_ids", [])

                # Get item details
                item = await MenuRepository.get_item_by_id(item_id)
                if item:
                    # Get modifier details
                    modifiers = []
                    modifier_total = Decimal("0")
                    if modifier_ids:
                        mod_data = await MenuRepository.get_modifiers_by_ids(modifier_ids)
                        for m in mod_data:
                            modifiers.append(CartItemModifier(
                                modifier_id=m["id"],
                                name_ar=m["name_ar"],
                                price_adjustment=Decimal(str(m["price_adjustment"])),
                            ))
                            modifier_total += Decimal(str(m["price_adjustment"]))

                    unit_price = Decimal(str(item["price"])) + modifier_total
                    total_price = unit_price * quantity

                    cart_item = CartItem(
                        menu_item_id=item_id,
                        item_name_ar=item["name_ar"],
                        quantity=quantity,
                        unit_price=unit_price,
                        total_price=total_price,
                        modifiers=modifiers,
                        special_instructions=cart_action.get("special_instructions"),
                    )
                    new_cart.append(cart_item)

            elif cart_action.get("type") == "remove":
                # Remove by index or item_id
                item_id = cart_action.get("item_id")
                if item_id:
                    new_cart = [c for c in new_cart if c.menu_item_id != item_id]

            elif cart_action.get("type") == "update":
                # Update quantity
                item_id = cart_action.get("item_id")
                quantity = cart_action.get("quantity", 1)
                for cart_item in new_cart:
                    if cart_item.menu_item_id == item_id:
                        cart_item.quantity = quantity
                        cart_item.total_price = cart_item.unit_price * quantity
                        break

            session_updates["cart"] = new_cart

            # Determine trigger
            if next_action == "checkout" and new_cart:
                trigger = Trigger.CHECKOUT
            elif next_action == "cancel":
                trigger = Trigger.CANCEL
            else:
                trigger = None  # Stay in ordering state

            return AgentResult(
                response_ar=response_ar,
                session_updates=session_updates,
                trigger=trigger,
                metadata={
                    "cart_action": cart_action,
                    "items_found": len(items_found),
                },
            )

        except Exception as e:
            # Default response on error
            if items_found:
                item_list = ", ".join([i.get("name_ar", "") for i in items_found[:3]])
                return AgentResult(
                    response_ar=f"لقيت لك: {item_list}. أي واحد تبي؟",
                    metadata={"error": str(e)},
                )
            return AgentResult(
                response_ar="وش تبي تطلب؟ قولي اسم الصنف وأساعدك.",
                metadata={"error": str(e)},
            )
