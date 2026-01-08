"""Restaurant status tools for FastMCP."""

from fastmcp import FastMCP

from sawt.utils.time_utils import (
    get_saudi_time,
    is_restaurant_open,
    get_next_opening_time,
    get_closing_time,
    format_time_ar,
    get_restaurant_status_message_ar,
)


def register_restaurant_status_tools(mcp: FastMCP) -> None:
    """Register restaurant status tools with the MCP server."""

    @mcp.tool()
    async def get_restaurant_status() -> dict:
        """
        التحقق من حالة المطعم (مفتوح/مغلق).
        ساعات العمل: من 9 صباحاً حتى 3 فجراً.

        Returns:
            dict with is_open, current_time, message_ar, next_event
        """
        now = get_saudi_time()
        is_open = is_restaurant_open()

        result = {
            "is_open": is_open,
            "current_time": now.strftime("%H:%M"),
            "current_time_ar": format_time_ar(now),
            "message_ar": get_restaurant_status_message_ar(),
        }

        if is_open:
            closing = get_closing_time()
            result["closes_at"] = closing.strftime("%H:%M")
            result["closes_at_ar"] = format_time_ar(closing)
        else:
            opening = get_next_opening_time()
            result["opens_at"] = opening.strftime("%H:%M")
            result["opens_at_ar"] = format_time_ar(opening)

        return result
