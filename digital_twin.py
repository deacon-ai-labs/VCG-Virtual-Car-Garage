def twin_snapshot(
    components: list[dict],
    specifications: list[dict],
) -> dict:
    """Summarise the structured digital twin for dashboard use."""

    root_systems = sorted(
        [
            component
            for component in components
            if (
                component.get("component_type") == "system"
                and component.get("parent_component_id") is None
            )
        ],
        key=lambda component: (
            component.get("sort_order", 0),
            component.get("name", ""),
        ),
    )

    mapped_components = [
        component
        for component in components
        if (
            component.get("component_type") != "system"
            and component.get("lifecycle_status") != "cancelled"
        )
    ]

    installed_components = [
        component
        for component in mapped_components
        if component.get("lifecycle_status") == "installed"
    ]

    verified_specs = [
        specification
        for specification in specifications
        if (
            specification.get("is_current", True)
            and specification.get("confidence") == "verified"
        )
    ]

    counts_by_system = {}

    for component in mapped_components:
        system_key = component.get("system_key")

        if not system_key:
            continue

        counts_by_system[system_key] = (
            counts_by_system.get(system_key, 0)
            + 1
        )

    return {
        "systems": root_systems,
        "system_count": len(root_systems),
        "mapped_component_count": len(mapped_components),
        "installed_component_count": len(installed_components),
        "verified_spec_count": len(verified_specs),
        "counts_by_system": counts_by_system,
    }


def build_snapshot(
    components: list[dict],
) -> dict:
    """Summarise non-system components used by the build workspace."""

    build_components = [
        component
        for component in components
        if (
            component.get("component_type") != "system"
            and component.get("lifecycle_status") != "cancelled"
        )
    ]

    installed = [
        component
        for component in build_components
        if component.get("lifecycle_status") == "installed"
    ]

    planned = [
        component
        for component in build_components
        if component.get("lifecycle_status") == "planned"
    ]

    removed = [
        component
        for component in build_components
        if component.get("lifecycle_status") == "removed"
    ]

    known_weight = sum(
        float(component["weight_kg"])
        * float(component.get("quantity") or 1)
        for component in build_components
        if component.get("weight_kg") is not None
        and component.get("lifecycle_status") in {
            "installed",
            "planned",
        }
    )

    return {
        "components": build_components,
        "installed": installed,
        "planned": planned,
        "removed": removed,
        "installed_count": len(installed),
        "planned_count": len(planned),
        "removed_count": len(removed),
        "known_weight_kg": known_weight,
    }


def format_build_context(
    components: list[dict],
) -> str:
    """Format the current physical build for Garage AI."""

    build = build_snapshot(
        components
    )

    active = [
        component
        for component in build["components"]
        if component.get("lifecycle_status") == "installed"
    ]

    if not active:
        return "No structured build components recorded."

    lines = []

    for component in active:
        details = [
            component.get("name")
            or "Unnamed component",
            f"status={component.get('lifecycle_status', 'unknown')}",
            f"system={component.get('system_key', 'unknown')}",
        ]

        if component.get("manufacturer"):
            details.append(
                f"manufacturer={component['manufacturer']}"
            )

        if component.get("part_number"):
            details.append(
                f"part_number={component['part_number']}"
            )

        if component.get("weight_kg") is not None:
            details.append(
                f"weight_kg={component['weight_kg']}"
            )

        if component.get("is_oem") is True:
            details.append("origin=OEM")
        elif component.get("is_oem") is False:
            details.append("origin=aftermarket")

        lines.append(
            "- " + "; ".join(
                str(detail)
                for detail in details
            )
        )

    return "\n".join(lines)
