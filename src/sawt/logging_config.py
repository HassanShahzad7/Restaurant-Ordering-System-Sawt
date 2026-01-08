"""Logging configuration for the ordering agent."""

import logging
import json
import sys
from datetime import datetime
from typing import Any

# Configure root logger with UTF-8 encoding for Arabic text
# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter(
    "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
))

# File handler - logs to sawt.log
file_handler = logging.FileHandler("sawt.log", encoding="utf-8", mode="a")
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
))

logging.basicConfig(
    level=logging.INFO,
    handlers=[console_handler, file_handler]
)

# Create specialized loggers
agent_logger = logging.getLogger("sawt.agent")
tool_logger = logging.getLogger("sawt.tool")
llm_logger = logging.getLogger("sawt.llm")
state_logger = logging.getLogger("sawt.state")
context_logger = logging.getLogger("sawt.context")  # For handoff context/token logging


def _serialize_value(value: Any) -> Any:
    """Serialize value for JSON logging."""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (list, dict)):
        return value
    return str(value) if not isinstance(value, (int, float, bool, type(None))) else value


def log_tool_call(tool_name: str, params: dict[str, Any]) -> None:
    """Log a tool invocation."""
    serialized_params = {k: _serialize_value(v) for k, v in params.items()}
    tool_logger.info(
        f"CALL {tool_name} | params={json.dumps(serialized_params, ensure_ascii=False)}"
    )


def log_tool_result(tool_name: str, result: dict[str, Any]) -> None:
    """Log a tool result."""
    # Truncate large results for logging
    result_str = json.dumps(result, ensure_ascii=False)
    if len(result_str) > 500:
        result_str = result_str[:500] + "..."
    tool_logger.info(f"RESULT {tool_name} | {result_str}")


def log_agent_handoff(from_agent: str, to_agent: str, summary: str) -> None:
    """Log agent handoff."""
    agent_logger.info(
        f"HANDOFF {from_agent} -> {to_agent} | summary={summary[:200]}..."
        if len(summary) > 200 else f"HANDOFF {from_agent} -> {to_agent} | summary={summary}"
    )


def log_agent_response(agent_name: str, response: str) -> None:
    """Log agent response."""
    truncated = response[:500] + "..." if len(response) > 500 else response
    agent_logger.info(f"RESPONSE {agent_name} | {truncated}")


def log_state_transition(from_state: str, to_state: str, trigger: str) -> None:
    """Log state machine transition."""
    state_logger.info(f"TRANSITION {from_state} -> {to_state} | trigger={trigger}")


def log_llm_call(model: str, prompt_tokens: int, completion_tokens: int) -> None:
    """Log LLM API call."""
    llm_logger.info(
        f"LLM_CALL model={model} | prompt_tokens={prompt_tokens} | completion_tokens={completion_tokens}"
    )


def log_error(component: str, error: str, context: dict[str, Any] | None = None) -> None:
    """Log an error."""
    ctx = json.dumps(context, ensure_ascii=False) if context else "{}"
    logging.getLogger(f"sawt.{component}").error(f"ERROR | {error} | context={ctx}")
