from __future__ import annotations

from datetime import date, datetime


def modification_items(
    modifications: str | None,
) -> list[str]:
    """Return clean, non-empty modification lines."""

    if not modifications:
        return []

    items = []

    for raw_line in modifications.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        while line[:1] in {
            "-",
            "•",
            "*",
        }:
            line = line[1:].strip()

        if line:
            items.append(line)

    return items


def _parse_due_date(
    value,
) -> date | None:
    """Return a date from Supabase date/datetime values."""

    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
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
    """Return whether a pending maintenance item is currently due."""

    if item.get("status") == "completed":
        return False

    today = today or date.today()

    due_mileage = item.get(
        "due_mileage"
    )

    if (
        due_mileage is not None
        and int(due_mileage)
        <= current_mileage
    ):
        return True

    due_date = _parse_due_date(
        item.get("due_date")
    )

    return (
        due_date is not None
        and due_date <= today
    )


def maintenance_due_label(
    item: dict,
) -> str:
    """Return a concise due label for one maintenance item."""

    due_mileage = item.get(
        "due_mileage"
    )
    due_date = _parse_due_date(
        item.get("due_date")
    )

    parts = []

    if due_mileage is not None:
        parts.append(
            f"{int(due_mileage):,} mi"
        )

    if due_date is not None:
        parts.append(
            due_date.strftime(
                "%d %b %Y"
            )
        )

    if not parts:
        return "No due point set"

    return " · ".join(parts)


def maintenance_snapshot(
    items: list[dict],
    current_mileage: int,
    today: date | None = None,
) -> dict:
    """Summarise maintenance without inventing a synthetic health score."""

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

    if overdue:
        state = "Attention"
        detail = (
            f"{len(overdue)} overdue"
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
        "pending_items": pending,
        "overdue_items": overdue,
    }
