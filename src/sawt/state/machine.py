"""State machine for conversation flow management."""

from enum import Enum
from typing import Any


class State(str, Enum):
    """Conversation states for the ordering flow."""

    S0_INIT = "S0_INIT"
    S1_INTENT = "S1_INTENT"
    S2_GREETING = "S2_GREETING"
    S3_LOCATION = "S3_LOCATION"
    S4_ORDERING = "S4_ORDERING"
    S5_CHECKOUT = "S5_CHECKOUT"
    S6_FINALIZED = "S6_FINALIZED"
    S_COMPLAINT = "S_COMPLAINT"
    S_FALLBACK = "S_FALLBACK"


class Intent(str, Enum):
    """User intent classifications."""

    ORDERING = "ordering"
    COMPLAINT = "complaint"
    INQUIRY = "inquiry"
    OTHER = "other"


class Trigger(str, Enum):
    """Triggers for state transitions."""

    # General triggers
    START = "start"
    RETRY = "retry"
    EXIT = "exit"

    # Intent-based triggers
    INTENT_ORDERING = "intent_ordering"
    INTENT_COMPLAINT = "intent_complaint"
    INTENT_INQUIRY = "intent_inquiry"
    INTENT_OTHER = "intent_other"

    # Flow triggers
    CONFIRM_ORDER = "confirm_order"
    NOT_ORDERING = "not_ordering"
    ADDRESS_VALID = "address_valid"
    ADDRESS_INVALID = "address_invalid"
    PICKUP_CHOSEN = "pickup_chosen"
    RESTAURANT_CLOSED = "restaurant_closed"
    CHECKOUT = "checkout"
    CONTINUE_ORDERING = "continue_ordering"
    ORDER_CONFIRMED = "order_confirmed"
    MODIFY_ORDER = "modify_order"
    CANCEL = "cancel"

    # Complaint handling
    RESOLVED = "resolved"
    ESCALATE = "escalate"


# State transition table
TRANSITIONS: dict[State, dict[Trigger, State]] = {
    State.S0_INIT: {
        Trigger.START: State.S1_INTENT,
    },
    State.S1_INTENT: {
        Trigger.INTENT_ORDERING: State.S2_GREETING,
        Trigger.INTENT_COMPLAINT: State.S_COMPLAINT,
        Trigger.INTENT_INQUIRY: State.S_FALLBACK,
        Trigger.INTENT_OTHER: State.S_FALLBACK,
    },
    State.S2_GREETING: {
        Trigger.CONFIRM_ORDER: State.S3_LOCATION,
        Trigger.NOT_ORDERING: State.S_FALLBACK,
        Trigger.RESTAURANT_CLOSED: State.S6_FINALIZED,
    },
    State.S3_LOCATION: {
        Trigger.ADDRESS_VALID: State.S4_ORDERING,
        Trigger.PICKUP_CHOSEN: State.S4_ORDERING,
        Trigger.RESTAURANT_CLOSED: State.S6_FINALIZED,
        Trigger.CANCEL: State.S0_INIT,
    },
    State.S4_ORDERING: {
        Trigger.CHECKOUT: State.S5_CHECKOUT,
        Trigger.CONTINUE_ORDERING: State.S4_ORDERING,
        Trigger.CANCEL: State.S0_INIT,
    },
    State.S5_CHECKOUT: {
        Trigger.ORDER_CONFIRMED: State.S6_FINALIZED,
        Trigger.MODIFY_ORDER: State.S4_ORDERING,
        Trigger.CANCEL: State.S0_INIT,
    },
    State.S6_FINALIZED: {
        Trigger.START: State.S1_INTENT,  # Allow starting new order
    },
    State.S_COMPLAINT: {
        Trigger.RESOLVED: State.S2_GREETING,
        Trigger.ESCALATE: State.S6_FINALIZED,
    },
    State.S_FALLBACK: {
        Trigger.RETRY: State.S1_INTENT,
        Trigger.EXIT: State.S6_FINALIZED,
        Trigger.INTENT_ORDERING: State.S2_GREETING,
    },
}


def get_next_state(current_state: State, trigger: Trigger) -> State | None:
    """
    Get the next state based on current state and trigger.

    Args:
        current_state: Current conversation state
        trigger: Trigger to apply

    Returns:
        Next state or None if transition is invalid
    """
    state_transitions = TRANSITIONS.get(current_state, {})
    return state_transitions.get(trigger)


def is_valid_transition(current_state: State, trigger: Trigger) -> bool:
    """Check if a transition is valid."""
    return get_next_state(current_state, trigger) is not None


def get_available_triggers(state: State) -> list[Trigger]:
    """Get all available triggers for a state."""
    return list(TRANSITIONS.get(state, {}).keys())


def intent_to_trigger(intent: Intent) -> Trigger:
    """Convert an intent classification to a state trigger."""
    mapping = {
        Intent.ORDERING: Trigger.INTENT_ORDERING,
        Intent.COMPLAINT: Trigger.INTENT_COMPLAINT,
        Intent.INQUIRY: Trigger.INTENT_INQUIRY,
        Intent.OTHER: Trigger.INTENT_OTHER,
    }
    return mapping.get(intent, Trigger.INTENT_OTHER)


def get_state_description_ar(state: State) -> str:
    """Get Arabic description of a state."""
    descriptions = {
        State.S0_INIT: "بداية المحادثة",
        State.S1_INTENT: "تحديد النية",
        State.S2_GREETING: "الترحيب",
        State.S3_LOCATION: "تحديد العنوان",
        State.S4_ORDERING: "اختيار الطلب",
        State.S5_CHECKOUT: "إتمام الطلب",
        State.S6_FINALIZED: "اكتمال الطلب",
        State.S_COMPLAINT: "معالجة الشكوى",
        State.S_FALLBACK: "استفسار عام",
    }
    return descriptions.get(state, state.value)


def get_agent_for_state(state: State) -> str:
    """Get the agent type that handles a state."""
    agent_mapping = {
        State.S0_INIT: "intent",
        State.S1_INTENT: "intent",
        State.S2_GREETING: "greeter",
        State.S3_LOCATION: "location",
        State.S4_ORDERING: "order",
        State.S5_CHECKOUT: "checkout",
        State.S6_FINALIZED: "summarizer",
        State.S_COMPLAINT: "complaint",
        State.S_FALLBACK: "fallback",
    }
    return agent_mapping.get(state, "fallback")
