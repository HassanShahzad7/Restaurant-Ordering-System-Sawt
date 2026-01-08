"""Session state models for Sawt."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass
class CartItemModifier:
    """Modifier applied to a cart item."""

    modifier_id: int
    name_ar: str
    price_adjustment: Decimal = Decimal("0")


@dataclass
class CartItem:
    """Item in the shopping cart."""

    menu_item_id: int
    item_name_ar: str
    quantity: int
    unit_price: Decimal
    total_price: Decimal
    modifiers: list[CartItemModifier] = field(default_factory=list)
    special_instructions: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "menu_item_id": self.menu_item_id,
            "item_name_ar": self.item_name_ar,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price),
            "total_price": float(self.total_price),
            "modifiers": [
                {
                    "modifier_id": m.modifier_id,
                    "modifier_name_ar": m.name_ar,
                    "price_adjustment": float(m.price_adjustment),
                }
                for m in self.modifiers
            ],
            "special_instructions": self.special_instructions,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CartItem":
        """Create from dictionary."""
        modifiers = [
            CartItemModifier(
                modifier_id=m["modifier_id"],
                name_ar=m.get("modifier_name_ar", m.get("name_ar", "")),
                price_adjustment=Decimal(str(m.get("price_adjustment", 0))),
            )
            for m in data.get("modifiers", [])
        ]

        return cls(
            menu_item_id=data["menu_item_id"],
            item_name_ar=data.get("item_name_ar", ""),
            quantity=data.get("quantity", 1),
            unit_price=Decimal(str(data.get("unit_price", 0))),
            total_price=Decimal(str(data.get("total_price", 0))),
            modifiers=modifiers,
            special_instructions=data.get("special_instructions"),
        )


@dataclass
class LocationInfo:
    """Delivery location information."""

    area_id: int | None = None
    area_name_ar: str | None = None
    street: str | None = None
    building: str | None = None
    delivery_notes: str | None = None

    def is_complete(self) -> bool:
        """Check if location info is complete enough for delivery."""
        return all([
            self.area_id is not None,
            self.area_name_ar,
            self.street,
            self.building,
        ])

    def to_address_string(self) -> str:
        """Convert to human-readable address string."""
        parts = []
        if self.area_name_ar:
            parts.append(self.area_name_ar)
        if self.street:
            parts.append(f"شارع {self.street}")
        if self.building:
            parts.append(f"مبنى {self.building}")
        return "، ".join(parts)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "area_id": self.area_id,
            "area_name_ar": self.area_name_ar,
            "street": self.street,
            "building": self.building,
            "delivery_notes": self.delivery_notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LocationInfo":
        """Create from dictionary."""
        return cls(
            area_id=data.get("area_id"),
            area_name_ar=data.get("area_name_ar"),
            street=data.get("street"),
            building=data.get("building"),
            delivery_notes=data.get("delivery_notes"),
        )


@dataclass
class SessionState:
    """Complete session state for a conversation."""

    session_id: str
    state: str = "S0_INIT"

    # Customer info
    customer_name: str | None = None
    customer_phone: str | None = None

    # Location info
    location: LocationInfo = field(default_factory=LocationInfo)
    order_type: str = "delivery"  # "delivery" or "pickup"

    # Cart
    cart: list[CartItem] = field(default_factory=list)

    # Promo
    applied_promo_code: str | None = None

    # Conversation
    conversation_history: list[dict[str, str]] = field(default_factory=list)
    conversation_summary_ar: str | None = None

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def get_cart_subtotal(self) -> Decimal:
        """Calculate cart subtotal."""
        return sum(item.total_price for item in self.cart)

    def get_cart_item_count(self) -> int:
        """Get total number of items in cart."""
        return sum(item.quantity for item in self.cart)

    def add_to_cart(self, item: CartItem) -> None:
        """Add an item to the cart."""
        # Check if same item exists (merge quantities)
        for existing in self.cart:
            if (
                existing.menu_item_id == item.menu_item_id
                and existing.modifiers == item.modifiers
                and existing.special_instructions == item.special_instructions
            ):
                existing.quantity += item.quantity
                existing.total_price += item.total_price
                return

        self.cart.append(item)

    def remove_from_cart(self, index: int) -> CartItem | None:
        """Remove an item from cart by index."""
        if 0 <= index < len(self.cart):
            return self.cart.pop(index)
        return None

    def clear_cart(self) -> None:
        """Clear all items from cart."""
        self.cart.clear()

    def add_message(self, role: str, content: str) -> None:
        """Add a message to conversation history."""
        self.conversation_history.append({"role": role, "content": content})

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            "session_id": self.session_id,
            "state": self.state,
            "customer_name": self.customer_name,
            "customer_phone": self.customer_phone,
            "delivery_address": self.location.to_address_string() if self.location else None,
            "delivery_area_id": self.location.area_id if self.location else None,
            "order_type": self.order_type,
            "cart": [item.to_dict() for item in self.cart],
            "applied_promo_code": self.applied_promo_code,
            "conversation_history": self.conversation_history,
            "conversation_summary_ar": self.conversation_summary_ar,
            "metadata": self.metadata,
        }

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> "SessionState":
        """Create from database row."""
        # Parse cart
        cart_data = row.get("cart", [])
        cart = [CartItem.from_dict(item) for item in cart_data]

        # Parse location
        location = LocationInfo(
            area_id=row.get("delivery_area_id"),
            area_name_ar=None,  # Will be fetched if needed
            street=None,
            building=None,
            delivery_notes=None,
        )

        return cls(
            session_id=row["id"],
            state=row.get("state", "S0_INIT"),
            customer_name=row.get("customer_name"),
            customer_phone=row.get("customer_phone"),
            location=location,
            order_type=row.get("order_type", "delivery"),
            cart=cart,
            applied_promo_code=row.get("applied_promo_code"),
            conversation_history=row.get("conversation_history", []),
            conversation_summary_ar=row.get("conversation_summary_ar"),
            metadata=row.get("metadata", {}),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )
