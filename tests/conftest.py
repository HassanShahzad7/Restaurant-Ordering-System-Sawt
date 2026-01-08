"""Pytest configuration and fixtures."""

import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_llm_client():
    """Mock OpenRouter client for unit tests."""
    client = MagicMock()
    client.complete = AsyncMock(return_value="هلا والله!")
    client.complete_json = AsyncMock(
        return_value={
            "intent": "ordering",
            "confidence": 0.9,
            "rationale_ar": "العميل يرحب",
        }
    )
    client.classify_intent = AsyncMock(
        return_value={
            "intent": "ordering",
            "confidence": 0.9,
        }
    )
    return client


@pytest.fixture
def sample_session_state():
    """Sample session state for testing."""
    from sawt.state.session_state import SessionState, LocationInfo

    return SessionState(
        session_id="test-session-123",
        state="S0_INIT",
        location=LocationInfo(),
    )


@pytest.fixture
def sample_cart_item():
    """Sample cart item for testing."""
    from decimal import Decimal
    from sawt.state.session_state import CartItem

    return CartItem(
        menu_item_id=1,
        item_name_ar="برجر لحم",
        quantity=2,
        unit_price=Decimal("28.00"),
        total_price=Decimal("56.00"),
    )


@pytest.fixture
def sample_menu_item():
    """Sample menu item dict for testing."""
    return {
        "id": 1,
        "name_ar": "برجر لحم كلاسيك",
        "name_en": "Classic Beef Burger",
        "description_ar": "برجر لحم بقري طازج",
        "category_ar": "برجر",
        "price": 28.00,
        "is_combo": False,
        "is_available": True,
    }


@pytest.fixture
def sample_covered_area():
    """Sample covered area dict for testing."""
    return {
        "id": 1,
        "name_ar": "حي النرجس",
        "name_en": "Al Narjis",
        "city": "Riyadh",
        "aliases_ar": ["النرجس", "نرجس"],
    }
