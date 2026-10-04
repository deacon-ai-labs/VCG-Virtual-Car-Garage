from __future__ import annotations


def _event_timestamp(
    item: dict,
) -> str:
    for key in (
        "occurred_at",
        "performed_at",
        "updated_at",
        "created_at",
    ):
        value = item.get(
            key
        )

        if value:
            return str(
                value
            )

    return ""


def vehicle_home_snapshot(
    maintenance: dict,
    diagnostics: dict,
    build_plan: dict,
    twin: dict,
    structured_build: dict,
    component_events: list[dict],
    maintenance_records: list[dict],
) -> dict:
    """Create an evidence-based overview of the selected vehicle."""

    attention = []

    overdue_count = int(
        maintenance.get(
            "overdue_count",
            0,
        )
        or 0
    )
    due_soon_count = int(
        maintenance.get(
            "due_soon_count",
            0,
        )
        or 0
    )

    if overdue_count:
        attention.append(
            {
                "severity": "error",
                "title": "Maintenance attention",
                "detail": (
                    f"{overdue_count} maintenance item"
                    f"{'' if overdue_count == 1 else 's'} "
                    "have reached a recorded due point."
                ),
                "workspace": "Maintenance OS",
            }
        )
    elif due_soon_count:
        attention.append(
            {
                "severity": "warning",
                "title": "Maintenance due soon",
                "detail": (
                    f"{due_soon_count} maintenance item"
                    f"{'' if due_soon_count == 1 else 's'} "
                    "are approaching a recorded due point."
                ),
                "workspace": "Maintenance OS",
            }
        )

    active_cases = int(
        diagnostics.get(
            "active_case_count",
            0,
        )
        or 0
    )

    if active_cases:
        attention.append(
            {
                "severity": "info",
                "title": "Active diagnostic investigation",
                "detail": (
                    f"{active_cases} diagnostic case"
                    f"{'' if active_cases == 1 else 's'} "
                    "remain open or under monitoring."
                ),
                "workspace": "Diagnostics",
            }
        )

    incompatible = int(
        build_plan.get(
            "incompatible_count",
            0,
        )
        or 0
    )
    compatibility_review = int(
        build_plan.get(
            "compatibility_review_count",
            0,
        )
        or 0
    )

    if incompatible:
        attention.append(
            {
                "severity": "error",
                "title": "Build compatibility conflict",
                "detail": (
                    f"{incompatible} planned installation"
                    f"{'' if incompatible == 1 else 's'} "
                    "are recorded as incompatible."
                ),
                "workspace": "Build Planner",
            }
        )
    elif compatibility_review:
        attention.append(
            {
                "severity": "warning",
                "title": "Build compatibility review",
                "detail": (
                    f"{compatibility_review} planned installation"
                    f"{'' if compatibility_review == 1 else 's'} "
                    "still need compatibility review."
                ),
                "workspace": "Build Planner",
            }
        )

    if not attention:
        attention.append(
            {
                "severity": "success",
                "title": "No recorded attention state",
                "detail": (
                    "VCG has no overdue maintenance, active diagnostic "
                    "case, or unresolved build-compatibility warning recorded."
                ),
                "workspace": None,
            }
        )

    activity = []

    for record in maintenance_records:
        activity.append(
            {
                "kind": "service",
                "title": (
                    record.get(
                        "title"
                    )
                    or "Maintenance record"
                ),
                "detail": (
                    "Service history"
                ),
                "timestamp": _event_timestamp(
                    record
                ),
            }
        )

    for event in component_events:
        event_type = str(
            event.get(
                "event_type"
            )
            or "event"
        ).replace(
            "_",
            " ",
        ).title()

        activity.append(
            {
                "kind": "component",
                "title": event_type,
                "detail": (
                    event.get(
                        "notes"
                    )
                    or "Digital-twin lifecycle event"
                ),
                "timestamp": _event_timestamp(
                    event
                ),
            }
        )

    activity = sorted(
        activity,
        key=lambda item: item[
            "timestamp"
        ],
        reverse=True,
    )[:6]

    return {
        "attention": attention,
        "recent_activity": activity,
        "maintenance_state": maintenance.get(
            "state",
            "Unknown",
        ),
        "maintenance_detail": maintenance.get(
            "detail",
            "No recorded state",
        ),
        "active_case_count": active_cases,
        "planned_change_count": int(
            build_plan.get(
                "active_count",
                0,
            )
            or 0
        ),
        "installed_component_count": int(
            structured_build.get(
                "installed_count",
                0,
            )
            or 0
        ),
        "system_count": int(
            twin.get(
                "system_count",
                0,
            )
            or 0
        ),
        "mapped_component_count": int(
            twin.get(
                "mapped_component_count",
                0,
            )
            or 0
        ),
        "verified_spec_count": int(
            twin.get(
                "verified_spec_count",
                0,
            )
            or 0
        ),
        "lifecycle_event_count": len(
            component_events
        ),
        "service_history_count": len(
            maintenance_records
        ),
    }
