"""Test the complete order flow end-to-end."""

import sys
import io

# Fix encoding for Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from langchain_core.messages import HumanMessage
from sawt.graph.workflow import graph
from sawt.graph.state import AgentState


def test_order_flow():
    """Test a complete order flow."""
    print("=" * 60)
    print("Testing Complete Order Flow")
    print("=" * 60)

    # Initial state
    state: AgentState = {
        "messages": [],
        "current_agent": "greeting",
        "session_id": "test-flow",
        "order_items": [],
        "subtotal": 0.0,
        "delivery_fee": 0.0,
        "discount": 0.0,
        "promo_code": None,
        "district": "",
        "district_validated": False,
        "customer_name": "",
        "customer_phone": "",
        "order_confirmed": False,
        "order_id": None,
        "handoff_summary_ar": "",
        "estimated_time": "",
        "order_type": "delivery",
    }

    # Conversation steps
    conversation = [
        "السلام عليكم",          # Greeting
        "أبي برجر",              # Order request
        "خلاص بس",               # Done ordering
        "استلام",                # Pickup
        "لا شكراً",              # No promo
        "محمد",                  # Name
        "0551234567",            # Phone
    ]

    for i, user_input in enumerate(conversation):
        print(f"\n{'='*60}")
        print(f"Step {i+1}: User says: {user_input}")
        print(f"Current agent: {state.get('current_agent', 'greeting')}")
        print("=" * 60)

        # Add user message
        state["messages"].append(HumanMessage(content=user_input))

        try:
            # Run the graph
            result = graph.invoke(state)

            # Update state
            state.update(result)

            # Get last AI message
            ai_messages = [m for m in state["messages"] if hasattr(m, "content") and m.type == "ai"]
            if ai_messages:
                last_response = ai_messages[-1].content
                print(f"\nAgent response: {last_response[:200]}..." if len(last_response) > 200 else f"\nAgent response: {last_response}")

            print(f"\nNew current agent: {state.get('current_agent', 'greeting')}")
            print(f"Order type: {state.get('order_type', 'N/A')}")
            print(f"District: {state.get('district', 'N/A')}")
            print(f"Order confirmed: {state.get('order_confirmed', False)}")

            if state.get("order_confirmed"):
                print("\n" + "=" * 60)
                print("ORDER CONFIRMED!")
                print(f"Order ID: {state.get('order_id')}")
                print("=" * 60)
                break

        except Exception as e:
            print(f"\nERROR: {e}")
            import traceback
            traceback.print_exc()
            break

    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_order_flow()
