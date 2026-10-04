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
        if component.get("component_type") != "system"
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
