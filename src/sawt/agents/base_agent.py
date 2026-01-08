"""Base agent class for Sawt agents."""

from abc import ABC, abstractmethod
from typing import Any

from sawt.llm.openrouter_client import OpenRouterClient
from sawt.state.session_state import SessionState
from sawt.state.machine import Trigger


class AgentResult:
    """Result from an agent's process method."""

    def __init__(
        self,
        response_ar: str,
        session_updates: dict[str, Any] | None = None,
        trigger: Trigger | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """
        Initialize agent result.

        Args:
            response_ar: Arabic response to send to user
            session_updates: Updates to apply to session state
            trigger: State machine trigger to fire
            metadata: Additional metadata
        """
        self.response_ar = response_ar
        self.session_updates = session_updates or {}
        self.trigger = trigger
        self.metadata = metadata or {}


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    def __init__(self, llm_client: OpenRouterClient):
        """
        Initialize the agent.

        Args:
            llm_client: OpenRouter client for LLM calls
        """
        self.llm = llm_client

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the agent name."""
        pass

    @property
    @abstractmethod
    def name_ar(self) -> str:
        """Get the agent name in Arabic."""
        pass

    @abstractmethod
    async def process(
        self,
        user_message: str,
        session: SessionState,
    ) -> AgentResult:
        """
        Process a user message.

        Args:
            user_message: The user's message
            session: Current session state

        Returns:
            AgentResult with response and updates
        """
        pass

    @abstractmethod
    def get_system_prompt(self, session: SessionState) -> str:
        """
        Get the system prompt for this agent.

        Args:
            session: Current session state for context

        Returns:
            System prompt string
        """
        pass

    def _build_messages(
        self,
        session: SessionState,
        user_message: str,
        include_history: bool = True,
    ) -> list[dict[str, str]]:
        """
        Build message list for LLM call.

        Args:
            session: Current session state
            user_message: Current user message
            include_history: Whether to include conversation history

        Returns:
            List of message dictionaries
        """
        messages = [
            {"role": "system", "content": self.get_system_prompt(session)}
        ]

        # Add summary if available
        if session.conversation_summary_ar:
            messages.append({
                "role": "system",
                "content": f"ملخص المحادثة:\n{session.conversation_summary_ar}",
            })

        # Add recent history
        if include_history and session.conversation_history:
            recent = session.conversation_history[-6:]
            for msg in recent:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                })

        # Add current message
        messages.append({"role": "user", "content": user_message})

        return messages
