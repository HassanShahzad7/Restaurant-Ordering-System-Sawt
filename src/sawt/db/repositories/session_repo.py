"""Session repository for database operations."""

import json
from datetime import datetime, timedelta
from typing import Any

import pytz

from sawt.config import get_settings
from sawt.db.connection import get_connection, get_transaction


class SessionRepository:
    """Repository for chat session operations."""

    @staticmethod
    async def get_session(session_id: str) -> dict[str, Any] | None:
        """Get a session by ID."""
        async with get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, state, customer_name, customer_phone, delivery_address,
                       delivery_area_id, order_type, cart, applied_promo_code,
                       conversation_history, conversation_summary_ar, metadata,
                       created_at, updated_at, expires_at
                FROM sessions
                WHERE id = $1
                """,
                session_id,
            )
            if not row:
                return None

            result = dict(row)
            # Parse JSONB fields
            result["cart"] = result["cart"] if result["cart"] else []
            result["conversation_history"] = (
                result["conversation_history"]
                if result["conversation_history"]
                else []
            )
            result["metadata"] = result["metadata"] if result["metadata"] else {}
            return result

    @staticmethod
    async def create_session(session_id: str) -> dict[str, Any]:
        """Create a new session."""
        settings = get_settings()
        now = datetime.now(pytz.timezone(settings.timezone))
        expires_at = now + timedelta(hours=settings.session_expiry_hours)

        async with get_transaction() as conn:
            await conn.execute(
                """
                INSERT INTO sessions (id, state, cart, conversation_history, metadata,
                                      created_at, updated_at, expires_at)
                VALUES ($1, 'S0_INIT', '[]'::jsonb, '[]'::jsonb, '{}'::jsonb,
                        $2, $2, $3)
                """,
                session_id,
                now,
                expires_at,
            )

        return await SessionRepository.get_session(session_id)  # type: ignore

    @staticmethod
    async def get_or_create_session(session_id: str) -> dict[str, Any]:
        """Get existing session or create a new one."""
        session = await SessionRepository.get_session(session_id)
        if session:
            # Check if expired
            settings = get_settings()
            now = datetime.now(pytz.timezone(settings.timezone))
            if session["expires_at"] and session["expires_at"] < now:
                # Session expired, create new one
                await SessionRepository.delete_session(session_id)
                return await SessionRepository.create_session(session_id)
            return session
        return await SessionRepository.create_session(session_id)

    @staticmethod
    async def update_session(session_id: str, updates: dict[str, Any]) -> bool:
        """Update session fields."""
        if not updates:
            return True

        settings = get_settings()
        now = datetime.now(pytz.timezone(settings.timezone))

        # Build update query dynamically
        set_clauses = ["updated_at = $2"]
        params: list[Any] = [session_id, now]
        param_idx = 3

        field_mapping = {
            "state": "state",
            "customer_name": "customer_name",
            "customer_phone": "customer_phone",
            "delivery_address": "delivery_address",
            "delivery_area_id": "delivery_area_id",
            "order_type": "order_type",
            "cart": "cart",
            "applied_promo_code": "applied_promo_code",
            "conversation_history": "conversation_history",
            "conversation_summary_ar": "conversation_summary_ar",
            "metadata": "metadata",
        }

        for key, column in field_mapping.items():
            if key in updates:
                value = updates[key]
                # Convert lists/dicts to JSON string for JSONB columns
                if key in ("cart", "conversation_history", "metadata"):
                    if isinstance(value, (list, dict)):
                        value = json.dumps(value)
                set_clauses.append(f"{column} = ${param_idx}")
                params.append(value)
                param_idx += 1

        query = f"""
            UPDATE sessions
            SET {', '.join(set_clauses)}
            WHERE id = $1
        """

        async with get_transaction() as conn:
            result = await conn.execute(query, *params)
            return result == "UPDATE 1"

    @staticmethod
    async def update_state(session_id: str, new_state: str) -> bool:
        """Update session state."""
        return await SessionRepository.update_session(session_id, {"state": new_state})

    @staticmethod
    async def update_cart(session_id: str, cart: list[dict[str, Any]]) -> bool:
        """Update session cart."""
        return await SessionRepository.update_session(session_id, {"cart": cart})

    @staticmethod
    async def add_to_conversation(
        session_id: str, role: str, content: str
    ) -> bool:
        """Add a message to conversation history."""
        session = await SessionRepository.get_session(session_id)
        if not session:
            return False

        history = session["conversation_history"]
        history.append({"role": role, "content": content})

        return await SessionRepository.update_session(
            session_id, {"conversation_history": history}
        )

    @staticmethod
    async def delete_session(session_id: str) -> bool:
        """Delete a session."""
        async with get_transaction() as conn:
            result = await conn.execute(
                "DELETE FROM sessions WHERE id = $1",
                session_id,
            )
            return result == "DELETE 1"

    @staticmethod
    async def cleanup_expired_sessions() -> int:
        """Delete all expired sessions. Returns count of deleted sessions."""
        settings = get_settings()
        now = datetime.now(pytz.timezone(settings.timezone))

        async with get_transaction() as conn:
            result = await conn.execute(
                "DELETE FROM sessions WHERE expires_at < $1",
                now,
            )
            # Parse "DELETE X" to get count
            return int(result.split()[-1]) if result else 0
