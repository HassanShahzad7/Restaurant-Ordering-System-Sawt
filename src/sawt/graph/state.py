"""State definitions for the LangGraph workflow."""

from typing import Annotated, Literal, TypedDict
from langgraph.graph.message import add_messages


class OrderItem(TypedDict):
    """Single item in the order."""
    item_id: str
    name_ar: str
    name_en: str
    quantity: int
    price: float
    notes: str


class AgentState(TypedDict):
    """State shared across all agents in the workflow."""

    # Message history (managed by LangGraph)
    messages: Annotated[list, add_messages]

    # Current agent in the workflow
    current_agent: Literal["greeting", "location", "order", "checkout", "end"]

    # Session information
    session_id: str

    # Customer information
    customer_name: str | None
    customer_phone: str | None

    # Intent (determined by greeting agent)
    intent: Literal["order", "complaint", "unknown"] | None

    # Location information
    district: str | None
    district_validated: bool
    delivery_fee: float
    estimated_time: str | None
    order_type: Literal["delivery", "pickup"]

    # Order information
    order_items: list[OrderItem]
    subtotal: float

    # Checkout information
    order_confirmed: bool
    order_id: str | None

    # Context for handoffs
    handoff_summary_ar: str

    # Backward routing flags (to track where user came from)
    came_from_checkout: bool
    came_from_order: bool

    # Logging/debugging
    token_count: int
    last_tool_calls: list[dict]


def create_initial_state(session_id: str) -> AgentState:
    """Create initial state for a new conversation."""
    return AgentState(
        messages=[],
        current_agent="greeting",
        session_id=session_id,
        customer_name=None,
        customer_phone=None,
        intent=None,
        district=None,
        district_validated=False,
        delivery_fee=0.0,
        estimated_time=None,
        order_type="delivery",
        order_items=[],
        subtotal=0.0,
        order_confirmed=False,
        order_id=None,
        handoff_summary_ar="",
        came_from_checkout=False,
        came_from_order=False,
        token_count=0,
        last_tool_calls=[],
    )
