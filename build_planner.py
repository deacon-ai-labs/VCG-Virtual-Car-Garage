from __future__ import annotations

ACTIVE_PLAN_STATUSES = {
    "wishlist",
    "planned",
    "ready",
}


def build_plan_snapshot(
    plan_items: list[dict],
    components: list[dict],
) -> dict:
    """Summarise current build and active/planned changes."""

    component_lookup = {
        str(component["id"]): component
        for component in components
        if component.get("component_type") != "system"
    }

    current_installed = [
        component
        for component in component_lookup.values()
        if component.get("lifecycle_status") == "installed"
    ]

    active_items = [
        item
        for item in plan_items
        if item.get("status") in ACTIVE_PLAN_STATUSES
    ]

    completed_items = [
        item
        for item in plan_items
        if item.get("status") == "completed"
    ]

    cancelled_items = [
        item
        for item in plan_items
        if item.get("status") == "cancelled"
    ]

    installs = [
        item
        for item in active_items
        if item.get("action") == "install"
    ]

    removals = [
        item
        for item in active_items
        if item.get("action") == "remove"
    ]

    estimated_cost = sum(
        float(item.get("estimated_cost_gbp") or 0)
        for item in active_items
    )

    current_known_weight = sum(
        float(component["weight_kg"])
        * float(component.get("quantity") or 1)
        for component in current_installed
        if component.get("weight_kg") is not None
    )

    known_weight_delta = 0.0
    unknown_weight_actions = 0

    for item in active_items:
        component = component_lookup.get(
            str(item.get("component_id"))
        )

        if not component:
            unknown_weight_actions += 1
            continue

        weight = component.get("weight_kg")

        if weight is None:
            unknown_weight_actions += 1
            continue

        total_weight = (
            float(weight)
            * float(component.get("quantity") or 1)
        )

        if item.get("action") == "install":
            known_weight_delta += total_weight
        elif item.get("action") == "remove":
            known_weight_delta -= total_weight

    compatibility_review = [
        item
        for item in installs
        if item.get("compatibility_status")
        in {"unknown", "needs_review"}
    ]

    incompatible = [
        item
        for item in installs
        if item.get("compatibility_status") == "incompatible"
    ]

    affected_systems = sorted(
        {
            component_lookup[
                str(item.get("component_id"))
            ].get("system_key", "unknown")
            for item in active_items
            if str(item.get("component_id"))
            in component_lookup
        }
    )

    return {
        "component_lookup": component_lookup,
        "current_installed": current_installed,
        "active_items": active_items,
        "completed_items": completed_items,
        "cancelled_items": cancelled_items,
        "installs": installs,
        "removals": removals,
        "current_installed_count": len(current_installed),
        "active_count": len(active_items),
        "install_count": len(installs),
        "removal_count": len(removals),
        "estimated_cost_gbp": estimated_cost,
        "current_known_weight_kg": current_known_weight,
        "known_weight_delta_kg": known_weight_delta,
        "projected_known_weight_kg": (
            current_known_weight + known_weight_delta
        ),
        "unknown_weight_actions": unknown_weight_actions,
        "compatibility_review_count": len(compatibility_review),
        "incompatible_count": len(incompatible),
        "affected_systems": affected_systems,
    }


def format_build_plan_context(
    plan_items: list[dict],
    components: list[dict],
) -> str:
    """Format active future changes for Garage AI."""

    snapshot = build_plan_snapshot(
        plan_items,
        components,
    )

    if not snapshot["active_items"]:
        return "No active build-plan changes."

    lines = []

    for item in snapshot["active_items"]:
        component = snapshot["component_lookup"].get(
            str(item.get("component_id")),
            {},
        )

        details = [
            component.get("name") or "Unnamed component",
            f"action={item.get('action', 'unknown')}",
            f"plan_status={item.get('status', 'unknown')}",
            f"system={component.get('system_key', 'unknown')}",
        ]

        if item.get("estimated_cost_gbp") is not None:
            details.append(
                f"estimated_cost_gbp={item['estimated_cost_gbp']}"
            )

        if component.get("weight_kg") is not None:
            details.append(
                f"weight_kg={component['weight_kg']}"
            )

        if item.get("action") == "install":
            details.append(
                "compatibility="
                + str(
                    item.get(
                        "compatibility_status",
                        "unknown",
                    )
                )
            )

            if item.get("compatibility_notes"):
                details.append(
                    "compatibility_notes="
                    + str(item["compatibility_notes"])
                )

        if item.get("notes"):
            details.append(
                "plan_notes="
                + str(item["notes"])
            )

        lines.append(
            "- " + "; ".join(details)
        )

    return "\n".join(lines)
