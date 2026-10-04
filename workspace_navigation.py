from __future__ import annotations


PRIMARY_WORKSPACES = (
    {
        "name": "Virtual Twin",
        "short_name": "Twin",
        "icon": "◇",
    },
    {
        "name": "Garage AI",
        "short_name": "Garage AI",
        "icon": "✦",
    },
)

CONTEXTUAL_WORKSPACES = (
    "Virtual Workshop",
    "Diagnostics",
    "Maintenance OS",
    "Build Planner",
)

LEGACY_WORKSPACE_ALIASES = {
    "Vehicle Home": "Virtual Twin",
}


def primary_workspace_names() -> tuple[str, ...]:
    return tuple(
        workspace["name"]
        for workspace in PRIMARY_WORKSPACES
    )


def allowed_workspace_names() -> tuple[str, ...]:
    return (
        *primary_workspace_names(),
        *CONTEXTUAL_WORKSPACES,
    )


def workspace_state_key(
    vehicle_id,
) -> str:
    return (
        "vehicle_workspace_mode_"
        f"{vehicle_id}"
    )


def normalize_workspace(
    value: str | None,
) -> str:
    normalized = LEGACY_WORKSPACE_ALIASES.get(
        value,
        value,
    )

    if normalized in allowed_workspace_names():
        return str(
            normalized
        )

    return "Virtual Twin"


def contextual_badges(
    maintenance: dict,
    diagnostics: dict,
    build_plan: dict,
) -> dict[str, int]:
    return {
        "Diagnostics": int(
            diagnostics.get(
                "active_case_count",
                0,
            )
            or 0
        ),
        "Maintenance OS": int(
            maintenance.get(
                "pending_count",
                0,
            )
            or 0
        ),
        "Build Planner": int(
            build_plan.get(
                "active_count",
                0,
            )
            or 0
        ),
    }
