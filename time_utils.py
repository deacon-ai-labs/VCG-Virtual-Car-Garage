from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def format_local_timestamp(
    timestamp: str | None,
    timezone_name: str | None,
) -> str:
    """Format an ISO UTC timestamp in the visitor's local timezone."""

    if not timestamp:
        return ""

    value = timestamp.replace(
        "Z",
        "+00:00",
    )

    parsed = datetime.fromisoformat(
        value
    )

    if parsed.tzinfo is None:
        parsed = parsed.replace(
            tzinfo=timezone.utc
        )

    try:
        local_zone = ZoneInfo(
            timezone_name or "UTC"
        )
    except ZoneInfoNotFoundError:
        local_zone = ZoneInfo("UTC")

    local_time = parsed.astimezone(
        local_zone
    )

    return local_time.strftime(
        "%d %b %H:%M"
    )
