"""Tests for state machine."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from sawt.state.machine import (
    State,
    Trigger,
    Intent,
    get_next_state,
    is_valid_transition,
    intent_to_trigger,
    get_agent_for_state,
)


class TestStateTransitions:
    """Tests for state transitions."""

    def test_init_to_intent(self):
        """Test transition from init to intent."""
        next_state = get_next_state(State.S0_INIT, Trigger.START)
        assert next_state == State.S1_INTENT

    def test_intent_ordering_to_greeting(self):
        """Test intent ordering leads to greeting."""
        next_state = get_next_state(State.S1_INTENT, Trigger.INTENT_ORDERING)
        assert next_state == State.S2_GREETING

    def test_intent_complaint_branch(self):
        """Test intent complaint leads to complaint state."""
        next_state = get_next_state(State.S1_INTENT, Trigger.INTENT_COMPLAINT)
        assert next_state == State.S_COMPLAINT

    def test_greeting_to_location(self):
        """Test greeting to location transition."""
        next_state = get_next_state(State.S2_GREETING, Trigger.CONFIRM_ORDER)
        assert next_state == State.S3_LOCATION

    def test_location_to_ordering(self):
        """Test location to ordering transition."""
        next_state = get_next_state(State.S3_LOCATION, Trigger.ADDRESS_VALID)
        assert next_state == State.S4_ORDERING

    def test_ordering_to_checkout(self):
        """Test ordering to checkout transition."""
        next_state = get_next_state(State.S4_ORDERING, Trigger.CHECKOUT)
        assert next_state == State.S5_CHECKOUT

    def test_checkout_to_finalized(self):
        """Test checkout to finalized transition."""
        next_state = get_next_state(State.S5_CHECKOUT, Trigger.ORDER_CONFIRMED)
        assert next_state == State.S6_FINALIZED


class TestValidTransition:
    """Tests for transition validation."""

    def test_valid_transition(self):
        """Test valid transition check."""
        assert is_valid_transition(State.S0_INIT, Trigger.START) is True

    def test_invalid_transition(self):
        """Test invalid transition check."""
        assert is_valid_transition(State.S0_INIT, Trigger.CHECKOUT) is False


class TestIntentToTrigger:
    """Tests for intent to trigger mapping."""

    def test_ordering_intent(self):
        """Test ordering intent maps correctly."""
        assert intent_to_trigger(Intent.ORDERING) == Trigger.INTENT_ORDERING

    def test_complaint_intent(self):
        """Test complaint intent maps correctly."""
        assert intent_to_trigger(Intent.COMPLAINT) == Trigger.INTENT_COMPLAINT


class TestAgentMapping:
    """Tests for state to agent mapping."""

    def test_intent_agent(self):
        """Test intent state maps to intent agent."""
        assert get_agent_for_state(State.S1_INTENT) == "intent"

    def test_greeter_agent(self):
        """Test greeting state maps to greeter agent."""
        assert get_agent_for_state(State.S2_GREETING) == "greeter"

    def test_order_agent(self):
        """Test ordering state maps to order agent."""
        assert get_agent_for_state(State.S4_ORDERING) == "order"
