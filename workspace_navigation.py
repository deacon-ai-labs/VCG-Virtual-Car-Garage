from __future__ import annotations


WORKSPACES = (
    {
        "name": "Vehicle Home",
        "short_name": "Home",
        "icon": "⌂",
    },
    {
        "name": "Garage AI",
        "short_name": "Garage AI",
        "icon": "✦",
    },
    {
        "name": "Virtual Workshop",
        "short_name": "Workshop",
        "icon": "◇",
    },
    {
        "name": "Diagnostics",
        "short_name": "Diagnostics",
        "icon": "△",
    },
    {
        "name": "Maintenance OS",
        "short_name": "Maintenance",
        "icon": "◉",
    },
    {
        "name": "Build Planner",
        "short_name": "Build",
        "icon": "＋",
    },
)


def workspace_names() -> tuple[str, ...]:
    return tuple(
        workspace["name"]
        for workspace in WORKSPACES
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
    if value in workspace_names():
        return str(
            value
        )

    return "Vehicle Home"


def workspace_badges(
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
