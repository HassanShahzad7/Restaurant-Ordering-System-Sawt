"""OpenRouter API client for LLM interactions."""

import json
from typing import Any

import httpx

from sawt.config import get_settings


class OpenRouterClient:
    """Client for OpenRouter API interactions."""

    def __init__(self):
        """Initialize the client."""
        self.settings = get_settings()
        self.base_url = self.settings.openrouter_base_url
        self.api_key = self.settings.openrouter_api_key
        self.model = self.settings.openrouter_model

    async def complete(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        response_format: dict | None = None,
    ) -> str:
        """
        Send a completion request to OpenRouter.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            response_format: Optional JSON schema for structured output

        Returns:
            The assistant's response text
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://sawt-restaurant.local",
            "X-Title": "Sawt Restaurant Agent",
        }

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_format:
            payload["response_format"] = response_format

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()

            return data["choices"][0]["message"]["content"]

    async def complete_json(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> dict[str, Any]:
        """
        Send a completion request expecting JSON response.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (lower for more deterministic)
            max_tokens: Maximum tokens in response

        Returns:
            Parsed JSON response as dictionary
        """
        response_text = await self.complete(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )

        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r"\{[\s\S]*\}", response_text)
            if json_match:
                return json.loads(json_match.group())
            raise ValueError(f"Could not parse JSON from response: {response_text}")

    async def classify_intent(self, user_message: str, context: str = "") -> dict[str, Any]:
        """
        Classify user intent using LLM.

        Args:
            user_message: The user's message
            context: Optional conversation context

        Returns:
            Dictionary with intent, confidence, and rationale
        """
        system_prompt = """أنت مصنف نوايا ذكي. مهمتك تحديد قصد العميل من رسالته.

## الأنواع المتاحة:
- ordering: العميل يريد طلب أكل (مثال: "أبي أطلب", "عندكم برجر؟", "وش القائمة؟", "السلام عليكم")
- complaint: العميل عنده شكوى (مثال: "طلبي متأخر", "الأكل بارد", "فيه مشكلة")
- inquiry: استفسار عام (مثال: "وين موقعكم؟", "كم ساعات العمل؟")
- other: أي شي ثاني

## التعليمات:
- إذا كانت الرسالة تحية أو سلام، صنفها كـ ordering لأن العميل غالباً يريد الطلب
- رد بصيغة JSON فقط

## صيغة الرد:
{"intent": "ordering|complaint|inquiry|other", "confidence": 0.0-1.0, "rationale_ar": "سبب قصير"}"""

        messages = [
            {"role": "system", "content": system_prompt},
        ]

        if context:
            messages.append({"role": "user", "content": f"السياق: {context}"})

        messages.append({"role": "user", "content": user_message})

        return await self.complete_json(messages, temperature=0.2)


# Singleton instance
_client: OpenRouterClient | None = None


def get_llm_client() -> OpenRouterClient:
    """Get or create the OpenRouter client instance."""
    global _client
    if _client is None:
        _client = OpenRouterClient()
    return _client
