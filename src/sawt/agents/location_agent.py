"""Location agent for collecting delivery address."""

from sawt.agents.base_agent import BaseAgent, AgentResult
from sawt.llm.openrouter_client import OpenRouterClient
from sawt.state.session_state import SessionState, LocationInfo
from sawt.state.machine import Trigger
from sawt.config import get_settings
from sawt.db.repositories.coverage_repo import CoverageRepository
from sawt.llm.prompt_templates.location import get_location_prompt


class LocationAgent(BaseAgent):
    """Agent for collecting and validating delivery location."""

    def __init__(self, llm_client: OpenRouterClient):
        super().__init__(llm_client)

    @property
    def name(self) -> str:
        return "location"

    @property
    def name_ar(self) -> str:
        return "مسؤول التوصيل"

    def get_system_prompt(self, session: SessionState) -> str:
        """Get the location prompt with current info."""
        settings = get_settings()

        # Format current location info
        if session.location and session.location.area_name_ar:
            current = f"""
- المنطقة: {session.location.area_name_ar or 'غير محدد'}
- الشارع: {session.location.street or 'غير محدد'}
- المبنى: {session.location.building or 'غير محدد'}
- ملاحظات: {session.location.delivery_notes or 'لا يوجد'}"""
        else:
            current = "لا توجد معلومات بعد"

        return get_location_prompt(current, float(settings.delivery_fee))

    async def process(
        self,
        user_message: str,
        session: SessionState,
    ) -> AgentResult:
        """Process location collection."""
        messages = self._build_messages(session, user_message)

        try:
            result = await self.llm.complete_json(messages, temperature=0.5)

            response_ar = result.get("response_ar", "وين تبينا نوصل لك؟")
            location_update = result.get("location_update", {})
            needs_check = result.get("needs_coverage_check", False)
            is_complete = result.get("is_complete", False)
            next_action = result.get("next_action", "continue")

            # Update location info
            new_location = session.location or LocationInfo()
            session_updates = {}

            if location_update.get("area_name_ar"):
                new_location.area_name_ar = location_update["area_name_ar"]
            if location_update.get("street"):
                new_location.street = location_update["street"]
            if location_update.get("building"):
                new_location.building = location_update["building"]
            if location_update.get("delivery_notes"):
                new_location.delivery_notes = location_update["delivery_notes"]

            # Check coverage if needed
            if needs_check and new_location.area_name_ar:
                is_covered, area_info = await CoverageRepository.check_coverage(
                    new_location.area_name_ar
                )

                if is_covered and area_info:
                    new_location.area_id = area_info["id"]
                    new_location.area_name_ar = area_info["name_ar"]
                    session_updates["order_type"] = "delivery"
                elif area_info and "suggestions" in area_info:
                    # Not covered but have suggestions
                    suggestions = area_info["suggestions"]
                    suggestion_names = [s["name_ar"] for s in suggestions[:3]]
                    response_ar = f"للأسف ما نغطي '{new_location.area_name_ar}'. هل تقصد: {', '.join(suggestion_names)}؟ أو تبي استلام من الفرع؟"
                    is_complete = False
                else:
                    response_ar = f"للأسف ما نغطي منطقة '{new_location.area_name_ar}'. تبي تستلم من الفرع بدلاً من التوصيل؟"
                    is_complete = False

            # Determine trigger
            if next_action == "pickup_chosen":
                trigger = Trigger.PICKUP_CHOSEN
                session_updates["order_type"] = "pickup"
            elif next_action == "address_valid" and new_location.is_complete():
                trigger = Trigger.ADDRESS_VALID
            elif next_action == "cancel":
                trigger = Trigger.CANCEL
            else:
                trigger = None  # Stay in location state

            return AgentResult(
                response_ar=response_ar,
                session_updates={
                    "location": new_location,
                    **session_updates,
                },
                trigger=trigger,
                metadata={
                    "is_complete": is_complete,
                    "location_update": location_update,
                },
            )

        except Exception as e:
            return AgentResult(
                response_ar="ممكن تعطيني عنوان التوصيل؟ أبي أعرف الحي والشارع ورقم المبنى.",
                metadata={"error": str(e)},
            )
