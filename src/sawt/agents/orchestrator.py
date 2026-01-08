"""Orchestrator for managing agent routing and state transitions."""

from typing import Any

from sawt.agents.base_agent import BaseAgent, AgentResult
from sawt.agents.intent_agent import IntentAgent
from sawt.agents.greeter_agent import GreeterAgent
from sawt.agents.location_agent import LocationAgent
from sawt.agents.order_agent import OrderAgent
from sawt.agents.checkout_agent import CheckoutAgent
from sawt.agents.summarizer_agent import SummarizerAgent
from sawt.llm.openrouter_client import OpenRouterClient, get_llm_client
from sawt.state.machine import (
    State,
    Trigger,
    get_next_state,
    get_agent_for_state,
    get_state_description_ar,
)
from sawt.state.session_state import SessionState
from sawt.db.repositories.session_repo import SessionRepository


class Orchestrator:
    """
    Main orchestrator for the restaurant ordering chatbot.

    Routes messages to appropriate agents based on conversation state,
    manages state transitions, and handles session persistence.
    """

    def __init__(self, llm_client: OpenRouterClient | None = None):
        """
        Initialize the orchestrator.

        Args:
            llm_client: OpenRouter client (uses singleton if not provided)
        """
        self.llm = llm_client or get_llm_client()

        # Initialize agents
        self.agents: dict[str, BaseAgent] = {
            "intent": IntentAgent(self.llm),
            "greeter": GreeterAgent(self.llm),
            "location": LocationAgent(self.llm),
            "order": OrderAgent(self.llm),
            "checkout": CheckoutAgent(self.llm),
            "summarizer": SummarizerAgent(self.llm),
        }

        # Track summarization frequency
        self._message_count: dict[str, int] = {}

    def _get_agent(self, state: State) -> BaseAgent:
        """Get the appropriate agent for a state."""
        agent_name = get_agent_for_state(state)
        return self.agents.get(agent_name, self.agents["greeter"])

    async def handle_message(
        self,
        session_id: str,
        user_message: str,
    ) -> str:
        """
        Handle an incoming user message.

        Args:
            session_id: Unique session identifier
            user_message: The user's message

        Returns:
            The agent's response in Arabic
        """
        # Load or create session
        session = await self._load_session(session_id)

        # Add user message to history
        session.add_message("user", user_message)

        # Handle initial state
        if session.state == State.S0_INIT.value:
            # Transition to intent detection
            session.state = State.S1_INTENT.value

        # Get current state
        current_state = State(session.state)

        # Special handling for intent state (runs silently, then routes)
        if current_state == State.S1_INTENT:
            intent_result = await self._run_intent_detection(session, user_message)

            # Apply trigger and transition
            if intent_result.trigger:
                next_state = get_next_state(current_state, intent_result.trigger)
                if next_state:
                    session.state = next_state.value
                    current_state = next_state

            # Apply any session updates
            await self._apply_session_updates(session, intent_result.session_updates)

        # Get the agent for current state
        agent = self._get_agent(current_state)

        # Process the message
        result = await agent.process(user_message, session)

        # Apply session updates
        await self._apply_session_updates(session, result.session_updates)

        # Handle state transition
        if result.trigger:
            next_state = get_next_state(current_state, result.trigger)
            if next_state:
                session.state = next_state.value

                # Generate summary on significant transitions
                if self._should_summarize(session_id, current_state, next_state):
                    await self._update_summary(session)

        # Add assistant response to history
        if result.response_ar:
            session.add_message("assistant", result.response_ar)

        # Save session
        await self._save_session(session)

        return result.response_ar

    async def _run_intent_detection(
        self,
        session: SessionState,
        user_message: str,
    ) -> AgentResult:
        """Run the intent detection agent."""
        intent_agent = self.agents["intent"]
        return await intent_agent.process(user_message, session)

    async def _apply_session_updates(
        self,
        session: SessionState,
        updates: dict[str, Any],
    ) -> None:
        """Apply updates to the session state."""
        if not updates:
            return

        for key, value in updates.items():
            if key == "cart" and value is not None:
                session.cart = value
            elif key == "location" and value is not None:
                session.location = value
            elif key == "customer_name" and value:
                session.customer_name = value
            elif key == "customer_phone" and value:
                session.customer_phone = value
            elif key == "order_type" and value:
                session.order_type = value
            elif key == "applied_promo_code":
                session.applied_promo_code = value
            elif key == "conversation_summary_ar" and value:
                session.conversation_summary_ar = value
            elif key == "metadata" and value:
                session.metadata.update(value)

    def _should_summarize(
        self,
        session_id: str,
        current_state: State,
        next_state: State,
    ) -> bool:
        """Determine if we should generate a summary."""
        # Track message count
        self._message_count[session_id] = self._message_count.get(session_id, 0) + 1

        # Summarize on significant state transitions
        significant_transitions = {
            (State.S2_GREETING, State.S3_LOCATION),
            (State.S3_LOCATION, State.S4_ORDERING),
            (State.S4_ORDERING, State.S5_CHECKOUT),
        }

        if (current_state, next_state) in significant_transitions:
            return True

        # Summarize every 5 messages
        if self._message_count[session_id] % 5 == 0:
            return True

        return False

    async def _update_summary(self, session: SessionState) -> None:
        """Update the conversation summary."""
        summarizer = self.agents["summarizer"]
        if isinstance(summarizer, SummarizerAgent):
            summary = await summarizer.generate_summary(session)
            session.conversation_summary_ar = summary

    async def _load_session(self, session_id: str) -> SessionState:
        """Load session from database or create new one."""
        session_data = await SessionRepository.get_or_create_session(session_id)
        return SessionState.from_db_row(session_data)

    async def _save_session(self, session: SessionState) -> None:
        """Save session to database."""
        updates = session.to_dict()
        # Remove session_id as it's the key, not an update
        updates.pop("session_id", None)
        await SessionRepository.update_session(session.session_id, updates)

    async def get_session_state(self, session_id: str) -> dict[str, Any]:
        """
        Get the current state of a session.

        Useful for debugging or displaying status.
        """
        session = await self._load_session(session_id)

        return {
            "session_id": session.session_id,
            "state": session.state,
            "state_description_ar": get_state_description_ar(State(session.state)),
            "customer_name": session.customer_name,
            "customer_phone": session.customer_phone,
            "order_type": session.order_type,
            "cart_items": len(session.cart),
            "cart_subtotal": float(session.get_cart_subtotal()),
            "location_complete": session.location.is_complete() if session.location else False,
            "has_promo": session.applied_promo_code is not None,
        }

    async def reset_session(self, session_id: str) -> None:
        """Reset a session to initial state."""
        await SessionRepository.delete_session(session_id)

    async def get_conversation_history(
        self,
        session_id: str,
    ) -> list[dict[str, str]]:
        """Get the conversation history for a session."""
        session = await self._load_session(session_id)
        return session.conversation_history


# Singleton instance
_orchestrator: Orchestrator | None = None


def get_orchestrator() -> Orchestrator:
    """Get or create the orchestrator singleton."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator


async def chat(session_id: str, message: str) -> str:
    """
    Simple chat interface.

    Args:
        session_id: Unique session identifier
        message: User's message

    Returns:
        Agent's response
    """
    orchestrator = get_orchestrator()
    return await orchestrator.handle_message(session_id, message)
