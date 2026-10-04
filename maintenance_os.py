from __future__ import annotations

from datetime import date, datetime, timedelta


def _parse_date(
    value,
) -> date | None:
    """Return a date from common Supabase date/datetime values."""

    if value is None:
        return None

    if isinstance(
        value,
        datetime,
    ):
        return value.date()

    if isinstance(
        value,
        date,
    ):
        return value

    try:
        return date.fromisoformat(
            str(value)[:10]
        )
    except ValueError:
        return None


def maintenance_is_overdue(
    item: dict,
    current_mileage: int,
    today: date | None = None,
) -> bool:
    """Return whether an open maintenance item has reached a due point."""

    if item.get("status") == "completed":
        return False

    today = today or date.today()

    due_mileage = item.get(
        "due_mileage"
    )

    if (
        due_mileage is not None
        and int(due_mileage)
        <= int(current_mileage)
    ):
        return True

    due_date = _parse_date(
        item.get("due_date")
    )

    return (
        due_date is not None
        and due_date <= today
    )


def maintenance_is_due_soon(
    item: dict,
    current_mileage: int,
    today: date | None = None,
    mileage_window: int = 1000,
    day_window: int = 30,
) -> bool:
    """Return whether an open item is approaching a recorded due point."""

    if maintenance_is_overdue(
        item,
        current_mileage,
        today=today,
    ):
        return False

    if item.get("status") == "completed":
        return False

    today = today or date.today()

    due_mileage = item.get(
        "due_mileage"
    )

    if due_mileage is not None:
        remaining_miles = (
            int(due_mileage)
            - int(current_mileage)
        )

        if (
            0 < remaining_miles
            <= mileage_window
        ):
            return True

    due_date = _parse_date(
        item.get("due_date")
    )

    if due_date is not None:
        remaining_days = (
            due_date
            - today
        ).days

        if (
            0 < remaining_days
            <= day_window
        ):
            return True

    return False


def maintenance_due_label(
    item: dict,
) -> str:
    """Return a concise due label for one maintenance schedule."""

    parts = []

    due_mileage = item.get(
        "due_mileage"
    )

    if due_mileage is not None:
        parts.append(
            f"{int(due_mileage):,} mi"
        )

    due_date = _parse_date(
        item.get("due_date")
    )

    if due_date is not None:
        parts.append(
            due_date.strftime(
                "%d %b %Y"
            )
        )

    if not parts:
        return "No due point set"

    return " · ".join(
        parts
    )


def maintenance_recurrence_label(
    item: dict,
) -> str:
    """Return a human-readable recurrence description."""

    parts = []

    interval_miles = item.get(
        "interval_miles"
    )

    if interval_miles is not None:
        parts.append(
            f"every {int(interval_miles):,} mi"
        )

    interval_months = item.get(
        "interval_months"
    )

    if interval_months is not None:
        months = int(
            interval_months
        )
        parts.append(
            f"every {months} month"
            f"{'' if months == 1 else 's'}"
        )

    if not parts:
        return "One-off"

    return " / ".join(
        parts
    )


def maintenance_health_snapshot(
    items: list[dict],
    records: list[dict],
    current_mileage: int,
    today: date | None = None,
) -> dict:
    """Summarise evidence-based maintenance state without a fake score."""

    today = today or date.today()

    pending = [
        item
        for item in items
        if item.get("status")
        != "completed"
    ]

    completed = [
        item
        for item in items
        if item.get("status")
        == "completed"
    ]

    overdue = [
        item
        for item in pending
        if maintenance_is_overdue(
            item,
            current_mileage,
            today=today,
        )
    ]

    due_soon = [
        item
        for item in pending
        if maintenance_is_due_soon(
            item,
            current_mileage,
            today=today,
        )
    ]

    unscheduled = [
        item
        for item in pending
        if (
            item.get("due_mileage")
            is None
            and item.get("due_date")
            is None
        )
    ]

    priority_rank = {
        "critical": 0,
        "high": 1,
        "normal": 2,
        "low": 3,
    }

    overdue_ids = {
        item.get("id")
        for item in overdue
    }

    due_soon_ids = {
        item.get("id")
        for item in due_soon
    }

    def action_rank(
        item: dict,
    ) -> tuple:
        item_id = item.get(
            "id"
        )

        if item_id in overdue_ids:
            stage = 0
        elif item_id in due_soon_ids:
            stage = 1
        else:
            stage = 2

        return (
            stage,
            priority_rank.get(
                item.get("priority"),
                2,
            ),
            item.get("sort_order", 0),
            item.get("title", ""),
        )

    next_actions = sorted(
        pending,
        key=action_rank,
    )

    lifetime_cost = sum(
        float(
            record.get("cost_gbp")
            or 0
        )
        for record in records
    )

    estimated_open_cost = sum(
        float(
            item.get(
                "estimated_cost_gbp"
            )
            or 0
        )
        for item in pending
    )

    if overdue:
        state = "Attention"
        detail = (
            f"{len(overdue)} overdue"
        )
    elif due_soon:
        state = "Due soon"
        detail = (
            f"{len(due_soon)} approaching"
        )
    elif pending:
        state = "Planned"
        detail = (
            f"{len(pending)} open"
        )
    else:
        state = "Clear"
        detail = "No open items"

    return {
        "state": state,
        "detail": detail,
        "pending_count": len(
            pending
        ),
        "completed_count": len(
            completed
        ),
        "overdue_count": len(
            overdue
        ),
        "due_soon_count": len(
            due_soon
        ),
        "unscheduled_count": len(
            unscheduled
        ),
        "history_count": len(
            records
        ),
        "lifetime_cost_gbp": (
            lifetime_cost
        ),
        "estimated_open_cost_gbp": (
            estimated_open_cost
        ),
        "pending_items": pending,
        "overdue_items": overdue,
        "due_soon_items": due_soon,
        "next_actions": next_actions,
    }
