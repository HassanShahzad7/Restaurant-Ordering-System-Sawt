"""Time and timezone utilities for Sawt."""

from datetime import datetime, time

import pytz

from sawt.config import get_settings


def get_saudi_time() -> datetime:
    """Get current time in Saudi Arabia timezone."""
    settings = get_settings()
    tz = pytz.timezone(settings.timezone)
    return datetime.now(tz)


def is_restaurant_open() -> bool:
    """
    Check if the restaurant is currently open.

    Operating hours: 9:00 AM to 3:00 AM next day (Saudi Arabia timezone).
    This means:
    - Open from 09:00 to 23:59
    - Open from 00:00 to 02:59
    - Closed from 03:00 to 08:59
    """
    settings = get_settings()
    now = get_saudi_time()
    hour = now.hour

    opening = settings.opening_hour  # 9
    closing = settings.closing_hour  # 3

    # Handle cross-midnight hours
    # Restaurant is open if:
    # - Current hour is >= opening hour (9) OR
    # - Current hour is < closing hour (3)
    if closing < opening:
        # Cross-midnight case (e.g., 9 AM to 3 AM)
        return hour >= opening or hour < closing
    else:
        # Same-day case (e.g., 9 AM to 11 PM)
        return opening <= hour < closing


def get_next_opening_time() -> datetime:
    """Get the next opening time if restaurant is closed."""
    settings = get_settings()
    now = get_saudi_time()
    hour = now.hour

    opening = settings.opening_hour  # 9

    if hour < opening:
        # Same day opening
        return now.replace(hour=opening, minute=0, second=0, microsecond=0)
    else:
        # Next day opening
        next_day = now.replace(hour=opening, minute=0, second=0, microsecond=0)
        return next_day.replace(day=now.day + 1)


def get_closing_time() -> datetime:
    """Get today's/tonight's closing time."""
    settings = get_settings()
    now = get_saudi_time()
    hour = now.hour

    closing = settings.closing_hour  # 3

    if hour >= settings.opening_hour:
        # Closing is tomorrow at 3 AM
        next_day = now.replace(hour=closing, minute=0, second=0, microsecond=0)
        return next_day.replace(day=now.day + 1)
    else:
        # Closing is today at 3 AM
        return now.replace(hour=closing, minute=0, second=0, microsecond=0)


def format_time_ar(dt: datetime) -> str:
    """Format datetime to Arabic-friendly string."""
    hour = dt.hour
    minute = dt.minute

    # Convert to 12-hour format
    if hour == 0:
        period = "صباحاً"
        display_hour = 12
    elif hour < 12:
        period = "صباحاً"
        display_hour = hour
    elif hour == 12:
        period = "مساءً"
        display_hour = 12
    else:
        period = "مساءً"
        display_hour = hour - 12

    if minute == 0:
        return f"{display_hour} {period}"
    else:
        return f"{display_hour}:{minute:02d} {period}"


def get_restaurant_status_message_ar() -> str:
    """Get a human-readable status message in Arabic."""
    if is_restaurant_open():
        closing = get_closing_time()
        return f"المطعم مفتوح حتى {format_time_ar(closing)}"
    else:
        opening = get_next_opening_time()
        return f"المطعم مغلق حالياً. يفتح الساعة {format_time_ar(opening)}"
