"""Base prompt template utilities."""

from string import Template
from typing import Any


class PromptTemplate:
    """Base class for prompt templates."""

    SYSTEM_TEMPLATE = Template("""
أنت $agent_name، مساعد ذكي في مطعم سعودي.

$role_description

## التعليمات:
$instructions

## القواعد:
$rules

## السياق الحالي:
$context
""")

    @classmethod
    def render(
        cls,
        agent_name: str,
        role_description: str,
        instructions: str,
        rules: str,
        context: str = "",
    ) -> str:
        """Render the prompt template."""
        return cls.SYSTEM_TEMPLATE.substitute(
            agent_name=agent_name,
            role_description=role_description,
            instructions=instructions,
            rules=rules,
            context=context if context else "لا يوجد سياق إضافي",
        ).strip()


def build_messages(
    system_prompt: str,
    conversation_history: list[dict[str, str]],
    user_message: str,
    summary: str | None = None,
) -> list[dict[str, str]]:
    """
    Build message list for LLM call.

    Args:
        system_prompt: The system prompt
        conversation_history: Previous messages
        user_message: Current user message
        summary: Optional conversation summary

    Returns:
        List of message dictionaries
    """
    messages = [{"role": "system", "content": system_prompt}]

    # Add summary if available
    if summary:
        messages.append({
            "role": "system",
            "content": f"ملخص المحادثة السابقة:\n{summary}",
        })

    # Add recent conversation history (last 6 messages)
    recent_history = conversation_history[-6:] if len(conversation_history) > 6 else conversation_history
    for msg in recent_history:
        messages.append({
            "role": msg["role"],
            "content": msg["content"],
        })

    # Add current user message
    messages.append({"role": "user", "content": user_message})

    return messages
