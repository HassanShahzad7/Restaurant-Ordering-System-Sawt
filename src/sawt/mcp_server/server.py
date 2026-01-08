"""FastMCP server setup for Sawt."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastmcp import FastMCP

from sawt.db.connection import init_db, close_db


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[dict]:
    """Manage server lifespan - initialize and cleanup resources."""
    # Startup: Initialize database pool
    await init_db()
    yield {}
    # Shutdown: Close database pool
    await close_db()


# Create the FastMCP server
mcp = FastMCP(
    name="sawt-restaurant",
    instructions="""
    أنت مساعد مطعم سعودي يتحدث باللهجة السعودية.
    استخدم الأدوات المتاحة للتحقق من حالة المطعم، البحث في القائمة،
    إدارة السلة، وإنشاء الطلبات.
    """,
    lifespan=lifespan,
)

# Import and register all tools
from sawt.mcp_server.tools.restaurant_status import register_restaurant_status_tools
from sawt.mcp_server.tools.numeral_normalizer import register_numeral_tools
from sawt.mcp_server.tools.coverage import register_coverage_tools
from sawt.mcp_server.tools.menu_search import register_menu_tools
from sawt.mcp_server.tools.cart_validation import register_cart_tools
from sawt.mcp_server.tools.promo import register_promo_tools
from sawt.mcp_server.tools.order import register_order_tools

# Register all tools with the server
register_restaurant_status_tools(mcp)
register_numeral_tools(mcp)
register_coverage_tools(mcp)
register_menu_tools(mcp)
register_cart_tools(mcp)
register_promo_tools(mcp)
register_order_tools(mcp)
