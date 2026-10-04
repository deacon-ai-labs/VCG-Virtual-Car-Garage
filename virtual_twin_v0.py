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


def virtual_twin_v0_snapshot(
    vehicle: dict,
    maintenance: dict,
    diagnostics: dict,
    build_plan: dict,
    structured_build: dict,
    twin: dict,
    component_events: list[dict],
    maintenance_records: list[dict],
) -> dict:
    """Create the deliberately small V0 Twin summary."""

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
                "detail": "Maintenance",
                "timestamp": _event_timestamp(
                    record
                ),
            }
        )

    for event in component_events:
        activity.append(
            {
                "kind": "component",
                "title": (
                    str(
                        event.get(
                            "event_type"
                        )
                        or "Vehicle update"
                    )
                    .replace(
                        "_",
                        " ",
                    )
                    .title()
                ),
                "detail": (
                    event.get(
                        "notes"
                    )
                    or "Build record"
                ),
                "timestamp": _event_timestamp(
                    event
                ),
            }
        )

    recent_activity = sorted(
        activity,
        key=lambda item: item[
            "timestamp"
        ],
        reverse=True,
    )[:3]

    installed = list(
        structured_build.get(
            "installed",
            []
        )
    )

    return {
        "mileage": int(
            vehicle.get(
                "mileage"
            )
            or 0
        ),
        "installed_count": int(
            structured_build.get(
                "installed_count",
                0,
            )
            or 0
        ),
        "maintenance_state": maintenance.get(
            "state",
            "Unknown",
        ),
        "maintenance_detail": maintenance.get(
            "detail",
            "No recorded state",
        ),
        "active_case_count": int(
            diagnostics.get(
                "active_case_count",
                0,
            )
            or 0
        ),
        "active_plan_count": int(
            build_plan.get(
                "active_count",
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
        "mapped_component_count": int(
            twin.get(
                "mapped_component_count",
                0,
            )
            or 0
        ),
        "installed_preview": installed[
            :5
        ],
        "recent_activity": recent_activity,
    }
