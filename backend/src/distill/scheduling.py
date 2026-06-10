"""Pure Delivery-Time matching logic, timezone-aware."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


def user_is_due(now_utc: datetime, delivery_time: str, tz_name: str) -> bool:
    if not delivery_time:
        return False
    try:
        tz = ZoneInfo(tz_name or "UTC")
    except Exception:
        tz = ZoneInfo("UTC")
    local_hhmm = now_utc.astimezone(tz).strftime("%H:%M")
    return local_hhmm == delivery_time[:5]
