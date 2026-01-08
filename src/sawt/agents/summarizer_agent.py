"""Summarizer agent for generating conversation summaries."""

from sawt.agents.base_agent import BaseAgent, AgentResult
from sawt.llm.openrouter_client import OpenRouterClient
from sawt.state.session_state import SessionState
from sawt.llm.prompt_templates.summarizer import get_summarizer_prompt


class SummarizerAgent(BaseAgent):
    """Agent for generating conversation summaries."""

    def __init__(self, llm_client: OpenRouterClient):
        super().__init__(llm_client)

    @property
    def name(self) -> str:
        return "summarizer"

    @property
    def name_ar(self) -> str:
        return "ملخص المحادثة"

    def get_system_prompt(self, session: SessionState) -> str:
        """Get the summarizer prompt."""
        # Format conversation history
        conversation = []
        for msg in session.conversation_history:
            role = "العميل" if msg["role"] == "user" else "المساعد"
            conversation.append(f"{role}: {msg['content']}")

        return get_summarizer_prompt("\n".join(conversation))

    async def process(
        self,
        user_message: str,
        session: SessionState,
    ) -> AgentResult:
        """Generate a summary of the conversation."""
        # This agent is typically called internally, not in response to user messages
        # It summarizes the conversation for handoffs between agents

        messages = [
            {"role": "system", "content": self.get_system_prompt(session)}
        ]

        try:
            summary = await self.llm.complete(messages, temperature=0.3, max_tokens=500)

            return AgentResult(
                response_ar=summary,  # The summary itself
                session_updates={
                    "conversation_summary_ar": summary,
                },
            )

        except Exception as e:
            # Generate a basic summary from session state
            parts = []

            if session.cart:
                items = ", ".join([item.item_name_ar for item in session.cart])
                parts.append(f"طلب: {items}")

            if session.location and session.location.area_name_ar:
                parts.append(f"موقع: {session.location.to_address_string()}")

            if session.customer_name:
                parts.append(f"اسم: {session.customer_name}")

            basic_summary = " | ".join(parts) if parts else "محادثة جديدة"

            return AgentResult(
                response_ar=basic_summary,
                session_updates={
                    "conversation_summary_ar": basic_summary,
                },
                metadata={"error": str(e)},
            )

    async def generate_summary(self, session: SessionState) -> str:
        """
        Generate a summary without processing a user message.

        This is called by the orchestrator to update summaries periodically.
        """
        result = await self.process("", session)
        return result.response_ar
