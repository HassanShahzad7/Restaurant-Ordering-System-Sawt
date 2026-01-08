"""Main entry point for Sawt restaurant ordering chatbot using LangGraph."""

import asyncio
import sys
import uuid
from typing import Any

# Fix Windows console encoding for Arabic text
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from langchain_core.messages import HumanMessage

from sawt.config import settings
from sawt.db.connection import init_db, close_db
from sawt.graph.state import create_initial_state
from sawt.graph.workflow import graph
from sawt.tools.menu_tools import load_menu_cache
from sawt.logging_config import log_state_transition


# Store active sessions
_sessions: dict[str, dict[str, Any]] = {}


async def load_menu_to_cache():
    """Load menu items from database into cache for tool usage."""
    from sawt.db.connection import DatabasePool

    try:
        pool = await DatabasePool.get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, name_ar, name_en, description_ar, category_ar, category_en, price, is_combo, is_available
                FROM menu_items
                WHERE is_available = TRUE
                """
            )
            items = [
                {
                    "id": str(row["id"]),
                    "name_ar": row["name_ar"],
                    "name_en": row.get("name_en", ""),
                    "description_ar": row.get("description_ar", ""),
                    "category": row.get("category_ar", ""),
                    "price": float(row["price"]),
                    "available": row.get("is_available", True),
                }
                for row in rows
            ]
            load_menu_cache(items)
            print(f"Loaded {len(items)} menu items into cache")
    except Exception as e:
        print(f"Warning: Could not load menu from database: {e}")
        print("Using empty menu cache - menu search will return no results")


def get_session_state(session_id: str) -> dict[str, Any]:
    """Get or create state for a session."""
    if session_id not in _sessions:
        _sessions[session_id] = create_initial_state(session_id)
    return _sessions[session_id]


def reset_session(session_id: str) -> None:
    """Reset a session state."""
    if session_id in _sessions:
        del _sessions[session_id]


async def process_message(session_id: str, user_message: str) -> str:
    """
    Process a user message through the LangGraph workflow.

    Args:
        session_id: Session identifier
        user_message: User's message in Arabic

    Returns:
        Agent response in Arabic
    """
    # Get current state
    state = get_session_state(session_id)

    # Add user message
    state["messages"].append(HumanMessage(content=user_message))

    # Run the graph with recursion limit to prevent infinite loops
    try:
        result = graph.invoke(state, {"recursion_limit": 10})

        # Update session state
        _sessions[session_id] = result

        # Get the last AI message
        messages = result.get("messages", [])
        for msg in reversed(messages):
            if hasattr(msg, "content") and msg.content and not hasattr(msg, "tool_calls"):
                return msg.content

        return "عذراً، حدث خطأ. حاول مرة ثانية."

    except Exception as e:
        print(f"Error processing message: {e}")
        return f"عذراً، حدث خطأ في النظام. الرجاء المحاولة مرة أخرى."


async def interactive_chat():
    """Run an interactive chat session."""
    print("=" * 60)
    print("  مرحباً بك في نظام طلبات المطعم - Sawt")
    print("  Welcome to the Restaurant Ordering System")
    print("=" * 60)
    print()
    print("Commands:")
    print("  'quit' or 'خروج' - Exit the chat")
    print("  'reset' - Start a new session")
    print("  'state' - Show current session state")
    print()
    print("=" * 60)
    print()

    # Initialize database
    print("Initializing...")
    try:
        await init_db()
        await load_menu_to_cache()
    except Exception as e:
        print(f"Warning: Database initialization failed: {e}")
        print("Running without database - some features may not work")

    # Generate session ID
    session_id = str(uuid.uuid4())[:8]
    print(f"Session ID: {session_id}")
    print(f"Model: {settings.openrouter_model}")
    print()

    try:
        while True:
            # Get user input
            try:
                user_input = input("أنت: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\nشكراً لك! مع السلامة.")
                break

            if not user_input:
                continue

            # Check for exit commands
            if user_input.lower() in ("quit", "exit", "خروج", "q"):
                print("\nشكراً لك! مع السلامة.")
                break

            # Check for reset command
            if user_input.lower() == "reset":
                reset_session(session_id)
                session_id = str(uuid.uuid4())[:8]
                print(f"\n[New Session: {session_id}]\n")
                continue

            # Check for state command
            if user_input.lower() == "state":
                state = get_session_state(session_id)
                print(f"\n[Current Agent: {state.get('current_agent', 'unknown')}]")
                print(f"[District: {state.get('district', 'N/A')}]")
                print(f"[Order Items: {len(state.get('order_items', []))}]")
                print(f"[Subtotal: {state.get('subtotal', 0)} SAR]")
                print(f"[Messages: {len(state.get('messages', []))}]\n")
                continue

            # Process message
            print("\nالمطعم: ", end="", flush=True)
            try:
                response = await process_message(session_id, user_input)
                print(response)
                print()
            except Exception as e:
                print(f"[Error: {e}]\n")

    finally:
        try:
            await close_db()
        except:
            pass


async def single_message(session_id: str, message: str) -> str:
    """
    Process a single message (for API usage).

    Args:
        session_id: Session identifier
        message: User message

    Returns:
        Agent response
    """
    await init_db()
    try:
        await load_menu_to_cache()
        return await process_message(session_id, message)
    finally:
        await close_db()


def main():
    """Main entry point."""
    asyncio.run(interactive_chat())


if __name__ == "__main__":
    main()
