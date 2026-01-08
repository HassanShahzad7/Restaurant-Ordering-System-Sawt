"""Intent classification agent."""

from sawt.agents.base_agent import BaseAgent, AgentResult
from sawt.llm.openrouter_client import OpenRouterClient
from sawt.state.session_state import SessionState
from sawt.state.machine import Trigger, Intent, intent_to_trigger


class IntentAgent(BaseAgent):
    """Agent for classifying user intent."""

    def __init__(self, llm_client: OpenRouterClient):
        super().__init__(llm_client)

    @property
    def name(self) -> str:
        return "intent"

    @property
    def name_ar(self) -> str:
        return "مصنف النوايا"

    def get_system_prompt(self, session: SessionState) -> str:
        """Get the intent classification prompt."""
        return """أنت مصنف نوايا ذكي. مهمتك تحديد قصد العميل من رسالته.

## الأنواع المتاحة:
- ordering: العميل يريد طلب أكل أو يرحب (مثال: "أبي أطلب", "السلام عليكم", "مرحبا", "عندكم برجر؟")
- complaint: العميل عنده شكوى واضحة (مثال: "طلبي متأخر", "الأكل بارد", "أبي أشتكي")
- inquiry: استفسار عام بدون نية طلب (مثال: "وين موقعكم؟", "كم ساعات العمل؟")
- other: أي شي ثاني غير واضح

## قواعد مهمة:
- التحيات والسلام تُصنف كـ ordering
- إذا العميل يسأل عن القائمة أو الأصناف = ordering
- الشكاوى يجب أن تكون واضحة وصريحة

## صيغة الرد (JSON):
{"intent": "ordering|complaint|inquiry|other", "confidence": 0.0-1.0, "rationale_ar": "سبب قصير"}"""

    async def process(
        self,
        user_message: str,
        session: SessionState,
    ) -> AgentResult:
        """Classify user intent."""
        messages = self._build_messages(session, user_message, include_history=False)

        try:
            result = await self.llm.complete_json(messages, temperature=0.2)

            intent_str = result.get("intent", "other")
            confidence = result.get("confidence", 0.5)

            # Map to Intent enum
            try:
                intent = Intent(intent_str)
            except ValueError:
                intent = Intent.OTHER

            # Get trigger
            trigger = intent_to_trigger(intent)

            # Build response (intent agent doesn't respond to user directly)
            return AgentResult(
                response_ar="",  # No direct response
                session_updates={
                    "metadata": {
                        **session.metadata,
                        "last_intent": intent_str,
                        "intent_confidence": confidence,
                    }
                },
                trigger=trigger,
                metadata={
                    "intent": intent_str,
                    "confidence": confidence,
                    "rationale": result.get("rationale_ar", ""),
                },
            )

        except Exception as e:
            # Default to ordering on error
            return AgentResult(
                response_ar="",
                trigger=Trigger.INTENT_ORDERING,
                metadata={"error": str(e)},
            )
