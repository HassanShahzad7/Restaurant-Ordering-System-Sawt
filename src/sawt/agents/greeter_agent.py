"""Greeter agent for welcoming customers."""

from sawt.agents.base_agent import BaseAgent, AgentResult
from sawt.llm.openrouter_client import OpenRouterClient
from sawt.state.session_state import SessionState
from sawt.state.machine import Trigger
from sawt.utils.time_utils import is_restaurant_open, get_restaurant_status_message_ar
from sawt.llm.prompt_templates.greeter import get_greeter_prompt


class GreeterAgent(BaseAgent):
    """Agent for greeting customers and confirming order intent."""

    def __init__(self, llm_client: OpenRouterClient):
        super().__init__(llm_client)

    @property
    def name(self) -> str:
        return "greeter"

    @property
    def name_ar(self) -> str:
        return "المضيف"

    def get_system_prompt(self, session: SessionState) -> str:
        """Get the greeter prompt with restaurant status."""
        status = get_restaurant_status_message_ar()
        return get_greeter_prompt(status)

    async def process(
        self,
        user_message: str,
        session: SessionState,
    ) -> AgentResult:
        """Process greeting and confirm order intent."""
        # Check if restaurant is open
        restaurant_open = is_restaurant_open()

        messages = self._build_messages(session, user_message)

        try:
            result = await self.llm.complete_json(messages, temperature=0.7)

            response_ar = result.get("response_ar", "هلا والله! كيف نقدر نخدمك؟")
            next_action = result.get("next_action", "confirm_order")

            # Determine trigger
            if not restaurant_open:
                trigger = Trigger.RESTAURANT_CLOSED
            elif next_action == "confirm_order":
                trigger = Trigger.CONFIRM_ORDER
            elif next_action == "not_ordering":
                trigger = Trigger.NOT_ORDERING
            elif next_action == "restaurant_closed":
                trigger = Trigger.RESTAURANT_CLOSED
            else:
                trigger = None  # Stay in current state

            return AgentResult(
                response_ar=response_ar,
                trigger=trigger,
                metadata={"next_action": next_action},
            )

        except Exception as e:
            # Default greeting on error
            if restaurant_open:
                return AgentResult(
                    response_ar="هلا والله! أهلاً وسهلاً فيك. تبي تطلب؟",
                    trigger=Trigger.CONFIRM_ORDER,
                    metadata={"error": str(e)},
                )
            else:
                status = get_restaurant_status_message_ar()
                return AgentResult(
                    response_ar=f"هلا فيك! {status}",
                    trigger=Trigger.RESTAURANT_CLOSED,
                    metadata={"error": str(e)},
                )
