from __future__ import annotations

from maintenance_os import (
    maintenance_due_label,
    maintenance_is_due_soon,
    maintenance_is_overdue,
)


def _component_lookup(
    components: list[dict],
) -> dict[str, dict]:
    return {
        str(component["id"]): component
        for component in components
    }


def _component_name(
    component_id,
    lookup: dict[str, dict],
) -> str:
    if component_id is None:
        return "Vehicle-level"

    component = lookup.get(
        str(component_id),
        {},
    )

    return component.get(
        "name",
        "Unknown component",
    )


def _format_vehicle_profile(
    vehicle: dict,
) -> str:
    return "\n".join(
        [
            f"Profile name: {vehicle.get('profile_name') or 'Unknown'}",
            f"Year: {vehicle.get('year') or 'Unknown'}",
            f"Manufacturer: {vehicle.get('manufacturer') or 'Unknown'}",
            f"Model: {vehicle.get('model') or 'Unknown'}",
            f"Engine: {vehicle.get('engine') or 'Unknown'}",
            f"Recorded mileage: {int(vehicle.get('mileage') or 0):,} mi",
        ]
    )


def _format_current_build(
    components: list[dict],
) -> str:
    installed = [
        component
        for component in components
        if (
            component.get("component_type") != "system"
            and component.get("lifecycle_status") == "installed"
        )
    ]

    if not installed:
        return "No installed structured components are recorded."

    lines = []

    for component in installed:
        details = [
            component.get("name")
            or "Unnamed component",
            f"system={component.get('system_key') or 'unknown'}",
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

        if component.get("installed_at"):
            details.append(
                f"installed_at={component['installed_at']}"
            )

        if component.get("installed_mileage") is not None:
            details.append(
                f"installed_mileage={component['installed_mileage']}"
            )

        details.append(
            (
                "origin=OEM"
                if component.get("is_oem") is True
                else (
                    "origin=aftermarket"
                    if component.get("is_oem") is False
                    else "origin=unknown"
                )
            )
        )

        lines.append(
            "- " + "; ".join(
                str(detail)
                for detail in details
            )
        )

    return "\n".join(lines)


def _format_build_plan(
    plan_items: list[dict],
    components: list[dict],
) -> str:
    active_statuses = {
        "wishlist",
        "planned",
        "ready",
    }

    lookup = _component_lookup(
        components
    )

    active = [
        item
        for item in plan_items
        if item.get("status") in active_statuses
    ]

    if not active:
        return "No active future build changes are recorded."

    lines = []

    for item in active:
        component = lookup.get(
            str(item.get("component_id")),
            {},
        )

        details = [
            component.get("name")
            or "Unknown component",
            f"action={item.get('action') or 'unknown'}",
            f"plan_status={item.get('status') or 'unknown'}",
            f"system={component.get('system_key') or 'unknown'}",
        ]

        if item.get("priority"):
            details.append(
                f"priority={item['priority']}"
            )

        if item.get("estimated_cost_gbp") is not None:
            details.append(
                f"estimated_cost_gbp={item['estimated_cost_gbp']}"
            )

        if item.get("target_date"):
            details.append(
                f"target_date={item['target_date']}"
            )

        if item.get("action") == "install":
            details.append(
                "compatibility_status="
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
            "- " + "; ".join(
                str(detail)
                for detail in details
            )
        )

    return "\n".join(lines)


def _format_verified_specs(
    specifications: list[dict],
    components: list[dict],
) -> str:
    lookup = _component_lookup(
        components
    )

    verified = [
        spec
        for spec in specifications
        if (
            spec.get("is_current", True)
            and spec.get("confidence") == "verified"
        )
    ]

    if not verified:
        return "No verified structured specifications are recorded."

    lines = []

    for spec in verified:
        value = (
            spec.get("value_text")
            if spec.get("value_text") is not None
            else spec.get("value_numeric")
        )

        details = [
            spec.get("label")
            or spec.get("spec_key")
            or "Unnamed specification",
            f"value={value}",
        ]

        if spec.get("unit"):
            details.append(
                f"unit={spec['unit']}"
            )

        details.append(
            "component="
            + _component_name(
                spec.get("component_id"),
                lookup,
            )
        )

        details.append(
            f"source_kind={spec.get('source_kind') or 'unknown'}"
        )

        if spec.get("source_reference"):
            details.append(
                "source_reference="
                + str(spec["source_reference"])
            )

        lines.append(
            "- " + "; ".join(
                str(detail)
                for detail in details
            )
        )

    return "\n".join(lines)


def _format_open_maintenance(
    maintenance_items: list[dict],
    current_mileage: int,
    components: list[dict],
) -> str:
    open_items = [
        item
        for item in maintenance_items
        if item.get("status") != "completed"
    ]

    if not open_items:
        return "No open maintenance items are recorded."

    def rank(
        item: dict,
    ) -> tuple:
        if maintenance_is_overdue(
            item,
            current_mileage,
        ):
            stage = 0
        elif maintenance_is_due_soon(
            item,
            current_mileage,
        ):
            stage = 1
        else:
            stage = 2

        priority_rank = {
            "critical": 0,
            "high": 1,
            "normal": 2,
            "low": 3,
        }

        return (
            stage,
            priority_rank.get(
                item.get("priority"),
                2,
            ),
            item.get("sort_order", 0),
            item.get("title", ""),
        )

    lookup = _component_lookup(
        components
    )

    lines = []

    for item in sorted(
        open_items,
        key=rank,
    )[:12]:
        if maintenance_is_overdue(
            item,
            current_mileage,
        ):
            state = "overdue"
        elif maintenance_is_due_soon(
            item,
            current_mileage,
        ):
            state = "due_soon"
        else:
            state = "open"

        details = [
            item.get("title")
            or "Unnamed maintenance item",
            f"state={state}",
            f"category={item.get('category') or 'service'}",
            f"priority={item.get('priority') or 'normal'}",
            f"due={maintenance_due_label(item)}",
            (
                "component="
                + _component_name(
                    item.get("twin_component_id"),
                    lookup,
                )
            ),
        ]

        if item.get("estimated_cost_gbp") is not None:
            details.append(
                f"estimated_cost_gbp={item['estimated_cost_gbp']}"
            )

        if item.get("notes"):
            details.append(
                "notes="
                + str(item["notes"])
            )

        lines.append(
            "- " + "; ".join(
                str(detail)
                for detail in details
            )
        )

    return "\n".join(lines)


def _format_service_history(
    maintenance_records: list[dict],
    components: list[dict],
) -> str:
    if not maintenance_records:
        return "No service-history records are stored."

    lookup = _component_lookup(
        components
    )

    lines = []

    for record in maintenance_records[:12]:
        details = [
            record.get("title")
            or "Unnamed maintenance record",
            f"performed_at={record.get('performed_at') or 'unknown'}",
            f"category={record.get('category') or 'service'}",
        ]

        if record.get("performed_mileage") is not None:
            details.append(
                f"mileage={record['performed_mileage']}"
            )

        if record.get("cost_gbp") is not None:
            details.append(
                f"cost_gbp={record['cost_gbp']}"
            )

        if record.get("provider"):
            details.append(
                "provider="
                + str(record["provider"])
            )

        details.append(
            "component="
            + _component_name(
                record.get("twin_component_id"),
                lookup,
            )
        )

        if record.get("notes"):
            details.append(
                "notes="
                + str(record["notes"])
            )

        if record.get("evidence_reference"):
            details.append(
                "evidence_reference="
                + str(record["evidence_reference"])
            )

        lines.append(
            "- " + "; ".join(
                str(detail)
                for detail in details
            )
        )

    return "\n".join(lines)


def _format_lifecycle_events(
    events: list[dict],
    components: list[dict],
) -> str:
    if not events:
        return "No component lifecycle events are recorded."

    lookup = _component_lookup(
        components
    )

    lines = []

    for event in events[:15]:
        details = [
            _component_name(
                event.get("component_id"),
                lookup,
            ),
            f"event={event.get('event_type') or 'unknown'}",
            f"occurred_at={str(event.get('occurred_at') or 'unknown')[:10]}",
        ]

        if event.get("mileage") is not None:
            details.append(
                f"mileage={event['mileage']}"
            )

        if event.get("notes"):
            details.append(
                "notes="
                + str(event["notes"])
            )

        lines.append(
            "- " + "; ".join(
                str(detail)
                for detail in details
            )
        )

    return "\n".join(lines)


def build_vehicle_intelligence_context(
    vehicle: dict,
    components: list[dict],
    specifications: list[dict],
    maintenance_items: list[dict],
    maintenance_records: list[dict],
    component_events: list[dict],
    build_plan_items: list[dict],
) -> str:
    """Create a bounded, source-labelled vehicle-state context for Garage AI."""

    current_mileage = int(
        vehicle.get("mileage")
        or 0
    )

    sections = [
        (
            "VEHICLE PROFILE — RECORDED APP STATE",
            _format_vehicle_profile(
                vehicle
            ),
        ),
        (
            "CURRENT PHYSICAL BUILD — RECORDED DIGITAL-TWIN STATE",
            _format_current_build(
                components
            ),
        ),
        (
            "ACTIVE FUTURE BUILD PLAN — INTENT ONLY, NOT PHYSICAL STATE",
            _format_build_plan(
                build_plan_items,
                components,
            ),
        ),
        (
            "VERIFIED STRUCTURED SPECIFICATIONS — CHECK SOURCE KIND/REFERENCE",
            _format_verified_specs(
                specifications,
                components,
            ),
        ),
        (
            "OPEN MAINTENANCE — RECORDED SCHEDULE/ADVISORY STATE",
            _format_open_maintenance(
                maintenance_items,
                current_mileage,
                components,
            ),
        ),
        (
            "SERVICE HISTORY — USER/APP-RECORDED PAST WORK",
            _format_service_history(
                maintenance_records,
                components,
            ),
        ),
        (
            "COMPONENT LIFECYCLE EVENTS — RECORDED HISTORY",
            _format_lifecycle_events(
                component_events,
                components,
            ),
        ),
    ]

    return "\n\n".join(
        (
            f"{heading}:\n{body}"
            for heading, body in sections
        )
    )
