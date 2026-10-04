from __future__ import annotations

from html import escape

from maintenance_os import (
    maintenance_is_due_soon,
    maintenance_is_overdue,
)


WORKSHOP_SYSTEM_ORDER = [
    "engine",
    "intake_fuel",
    "cooling",
    "electrical",
    "transmission_driveline",
    "suspension_steering",
    "brakes",
    "wheels_tyres",
    "interior_safety",
    "exhaust",
    "body_exterior",
    "fluids_consumables",
]


SYSTEM_POSITIONS = {
    "engine": (450, 210, 450, 55),
    "intake_fuel": (345, 245, 160, 150),
    "cooling": (560, 250, 735, 165),
    "electrical": (565, 355, 735, 310),
    "transmission_driveline": (450, 405, 735, 405),
    "suspension_steering": (330, 430, 140, 405),
    "brakes": (310, 575, 135, 565),
    "wheels_tyres": (620, 515, 750, 520),
    "interior_safety": (450, 510, 450, 900),
    "exhaust": (550, 650, 735, 685),
    "body_exterior": (450, 760, 145, 760),
    "fluids_consumables": (340, 325, 145, 300),
}


def _component_lookup(
    components: list[dict],
) -> dict[str, dict]:
    return {
        str(component["id"]): component
        for component in components
        if component.get("lifecycle_status") != "cancelled"
    }


def workshop_snapshot(
    components: list[dict],
    plan_items: list[dict],
    maintenance_items: list[dict],
    maintenance_records: list[dict],
    specifications: list[dict],
    current_mileage: int,
) -> dict:
    """Build a system-by-system view of the vehicle digital twin."""

    lookup = _component_lookup(
        components
    )

    roots = {
        component.get("system_key"): component
        for component in components
        if (
            component.get("component_type") == "system"
            and component.get("parent_component_id") is None
        )
    }

    active_plan_statuses = {
        "wishlist",
        "planned",
        "ready",
    }

    systems = []

    for system_key in WORKSHOP_SYSTEM_ORDER:
        root = roots.get(
            system_key
        )

        if not root:
            continue

        system_components = [
            component
            for component in components
            if (
                component.get("component_type") != "system"
                and component.get("system_key") == system_key
                and component.get("lifecycle_status") != "cancelled"
            )
        ]

        component_ids = {
            str(component["id"])
            for component in system_components
        }
        component_ids.add(
            str(root["id"])
        )

        active_plans = [
            item
            for item in plan_items
            if (
                item.get("status") in active_plan_statuses
                and str(item.get("component_id")) in component_ids
            )
        ]

        linked_maintenance = [
            item
            for item in maintenance_items
            if (
                item.get("status") != "completed"
                and str(item.get("twin_component_id")) in component_ids
            )
        ]

        overdue_items = [
            item
            for item in linked_maintenance
            if maintenance_is_overdue(
                item,
                current_mileage,
            )
        ]

        due_soon_items = [
            item
            for item in linked_maintenance
            if maintenance_is_due_soon(
                item,
                current_mileage,
            )
        ]

        history = [
            record
            for record in maintenance_records
            if str(record.get("twin_component_id")) in component_ids
        ]

        verified_specs = [
            spec
            for spec in specifications
            if (
                spec.get("confidence") == "verified"
                and spec.get("is_current", True)
                and str(spec.get("component_id")) in component_ids
            )
        ]

        installed = [
            component
            for component in system_components
            if component.get("lifecycle_status") == "installed"
        ]

        planned_components = [
            component
            for component in system_components
            if component.get("lifecycle_status") == "planned"
        ]

        removed = [
            component
            for component in system_components
            if component.get("lifecycle_status") == "removed"
        ]

        known_installed_weight = sum(
            float(component["weight_kg"])
            * float(component.get("quantity") or 1)
            for component in installed
            if component.get("weight_kg") is not None
        )

        if overdue_items:
            state = "attention"
        elif active_plans:
            state = "planned"
        elif installed:
            state = "active"
        else:
            state = "empty"

        systems.append(
            {
                "system_key": system_key,
                "name": root.get(
                    "name",
                    system_key,
                ),
                "root": root,
                "installed": installed,
                "planned_components": planned_components,
                "removed": removed,
                "active_plans": active_plans,
                "maintenance_items": linked_maintenance,
                "overdue_items": overdue_items,
                "due_soon_items": due_soon_items,
                "maintenance_history": history,
                "verified_specs": verified_specs,
                "installed_count": len(installed),
                "planned_count": len(active_plans),
                "maintenance_count": len(linked_maintenance),
                "history_count": len(history),
                "verified_spec_count": len(verified_specs),
                "known_installed_weight_kg": known_installed_weight,
                "state": state,
            }
        )

    return {
        "systems": systems,
        "system_lookup": {
            system[
                "system_key"
            ]: system
            for system in systems
        },
        "installed_component_count": sum(
            system[
                "installed_count"
            ]
            for system in systems
        ),
        "active_plan_count": sum(
            system[
                "planned_count"
            ]
            for system in systems
        ),
        "maintenance_attention_count": sum(
            len(
                system[
                    "overdue_items"
                ]
            )
            for system in systems
        ),
        "systems_with_activity": sum(
            1
            for system in systems
            if (
                system[
                    "installed_count"
                ]
                or system[
                    "planned_count"
                ]
                or system[
                    "maintenance_count"
                ]
            )
        ),
        "component_lookup": lookup,
    }


def workshop_blueprint_html(
    snapshot: dict,
    selected_system_key: str,
) -> str:
    """Render a technical top-down vehicle schematic as self-contained HTML."""

    states = {
        system[
            "system_key"
        ]: system[
            "state"
        ]
        for system in snapshot[
            "systems"
        ]
    }

    names = {
        system[
            "system_key"
        ]: system[
            "name"
        ]
        for system in snapshot[
            "systems"
        ]
    }

    counts = {
        system[
            "system_key"
        ]: (
            system[
                "installed_count"
            ],
            system[
                "planned_count"
            ],
            system[
                "maintenance_count"
            ],
        )
        for system in snapshot[
            "systems"
        ]
    }

    hotspot_svg = []

    for system_key in WORKSHOP_SYSTEM_ORDER:
        if system_key not in names:
            continue

        x, y, label_x, label_y = SYSTEM_POSITIONS[
            system_key
        ]

        selected = (
            system_key
            == selected_system_key
        )

        state = states.get(
            system_key,
            "empty",
        )

        installed_count, plan_count, maintenance_count = (
            counts[
                system_key
            ]
        )

        if state == "attention":
            fill = "#FF6B4A"
        elif state == "planned":
            fill = "#F0B35A"
        elif state == "active":
            fill = "#5E9BCB"
        else:
            fill = "#536273"

        radius = (
            13
            if selected
            else 9
        )

        stroke = (
            "#FFFFFF"
            if selected
            else "#0B1118"
        )

        label_anchor = (
            "middle"
            if 300 <= label_x <= 600
            else (
                "start"
                if label_x > 600
                else "end"
            )
        )

        hotspot_svg.append(
            f"""
            <line
                x1="{x}" y1="{y}"
                x2="{label_x}" y2="{label_y}"
                stroke="#3B4B5D"
                stroke-width="1.5"
                stroke-dasharray="5 5"
            />
            <circle
                cx="{x}" cy="{y}" r="{radius}"
                fill="{fill}"
                stroke="{stroke}"
                stroke-width="{3 if selected else 2}"
            />
            <text
                x="{label_x}"
                y="{label_y - 7}"
                fill="#F4F7FA"
                font-size="14"
                font-weight="700"
                text-anchor="{label_anchor}"
            >
                {escape(str(names[system_key]))}
            </text>
            <text
                x="{label_x}"
                y="{label_y + 12}"
                fill="#91A0AE"
                font-size="11"
                text-anchor="{label_anchor}"
            >
                {installed_count} fitted · {plan_count} planned · {maintenance_count} maint.
            </text>
            """
        )

    return f"""
    <div class="vcg-workshop-blueprint">
        <style>
            .vcg-workshop-blueprint {{
                border: 1px solid #283646;
                border-radius: 18px;
                background:
                    radial-gradient(
                        circle at 50% 35%,
                        rgba(255,107,74,0.07),
                        transparent 28%
                    ),
                    linear-gradient(
                        180deg,
                        #101821,
                        #0C131B
                    );
                overflow: hidden;
                padding: 0.45rem;
            }}
            .vcg-workshop-blueprint svg {{
                width: 100%;
                height: auto;
                display: block;
            }}
        </style>
        <svg
            viewBox="0 0 900 960"
            role="img"
            aria-label="Vehicle digital twin workshop schematic"
        >
            <defs>
                <linearGradient id="bodyFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="#1B2835"/>
                    <stop offset="100%" stop-color="#111A24"/>
                </linearGradient>
            </defs>

            <rect x="0" y="0" width="900" height="960" fill="transparent"/>

            <text
                x="450" y="30"
                fill="#6F7F90"
                font-size="11"
                text-anchor="middle"
                letter-spacing="3"
            >
                FRONT
            </text>

            <path
                d="
                    M365 92
                    C330 118 310 170 302 235
                    L285 365
                    C275 430 280 540 292 625
                    L312 790
                    C320 850 355 885 400 900
                    L500 900
                    C545 885 580 850 588 790
                    L608 625
                    C620 540 625 430 615 365
                    L598 235
                    C590 170 570 118 535 92
                    C500 67 400 67 365 92
                    Z
                "
                fill="url(#bodyFill)"
                stroke="#42566A"
                stroke-width="4"
            />

            <path
                d="
                    M365 275
                    C390 250 510 250 535 275
                    L555 385
                    L345 385
                    Z
                "
                fill="#0B1118"
                stroke="#304254"
                stroke-width="3"
            />

            <path
                d="
                    M345 420
                    L555 420
                    L565 635
                    L335 635
                    Z
                "
                fill="#0D151E"
                stroke="#304254"
                stroke-width="3"
            />

            <path
                d="
                    M340 675
                    L560 675
                    L545 805
                    C520 830 380 830 355 805
                    Z
                "
                fill="#0B1118"
                stroke="#304254"
                stroke-width="3"
            />

            <rect x="260" y="250" width="35" height="155" rx="15" fill="#090E14" stroke="#394B5D" stroke-width="3"/>
            <rect x="605" y="250" width="35" height="155" rx="15" fill="#090E14" stroke="#394B5D" stroke-width="3"/>
            <rect x="260" y="585" width="35" height="155" rx="15" fill="#090E14" stroke="#394B5D" stroke-width="3"/>
            <rect x="605" y="585" width="35" height="155" rx="15" fill="#090E14" stroke="#394B5D" stroke-width="3"/>

            <line x1="450" y1="92" x2="450" y2="900" stroke="#263646" stroke-width="1" stroke-dasharray="7 8"/>
            <line x1="310" y1="405" x2="590" y2="405" stroke="#263646" stroke-width="1"/>
            <line x1="305" y1="650" x2="595" y2="650" stroke="#263646" stroke-width="1"/>

            {"".join(hotspot_svg)}

            <g transform="translate(310,922)">
                <circle cx="0" cy="0" r="6" fill="#5E9BCB"/>
                <text x="13" y="4" fill="#91A0AE" font-size="11">current</text>
                <circle cx="100" cy="0" r="6" fill="#F0B35A"/>
                <text x="113" y="4" fill="#91A0AE" font-size="11">planned</text>
                <circle cx="205" cy="0" r="6" fill="#FF6B4A"/>
                <text x="218" y="4" fill="#91A0AE" font-size="11">attention</text>
            </g>
        </svg>
    </div>
    """


def system_status_label(
    system: dict,
) -> str:
    """Return a concise inspector status label."""

    if system[
        "overdue_items"
    ]:
        return "Maintenance attention"

    if system[
        "active_plans"
    ]:
        return "Build activity"

    if system[
        "installed"
    ]:
        return "Current build"

    return "No mapped activity"
