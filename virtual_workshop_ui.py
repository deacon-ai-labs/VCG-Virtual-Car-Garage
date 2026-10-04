from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as st_components

from maintenance_os import (
    maintenance_due_label,
    maintenance_is_due_soon,
    maintenance_is_overdue,
)
from virtual_workshop import (
    system_status_label,
    workshop_blueprint_html,
    workshop_snapshot,
)


def _switch_workspace(
    workspace_state_key: str,
    workspace_name: str,
) -> None:
    st.session_state[
        workspace_state_key
    ] = workspace_name


def _component_name(
    component_id,
    component_lookup: dict[str, dict],
) -> str:
    component = component_lookup.get(
        str(
            component_id
        ),
        {},
    )

    return component.get(
        "name",
        "Unknown component",
    )


def render_virtual_workshop(
    vehicle: dict,
    components: list[dict],
    plan_items: list[dict],
    maintenance_items: list[dict],
    maintenance_records: list[dict],
    specifications: list[dict],
    workspace_state_key: str,
) -> None:
    """Render the first visual digital-twin workshop."""

    current_mileage = int(
        vehicle.get(
            "mileage"
        )
        or 0
    )

    snapshot = workshop_snapshot(
        components,
        plan_items,
        maintenance_items,
        maintenance_records,
        specifications,
        current_mileage,
    )

    systems = snapshot[
        "systems"
    ]

    if not systems:
        st.warning(
            "This vehicle does not have a digital-twin system scaffold yet."
        )
        return

    selection_key = (
        "workshop_selected_system_"
        f"{vehicle['id']}"
    )

    valid_keys = [
        system[
            "system_key"
        ]
        for system in systems
    ]

    if (
        selection_key
        not in st.session_state
        or st.session_state[
            selection_key
        ]
        not in valid_keys
    ):
        default_key = (
            "engine"
            if "engine" in valid_keys
            else valid_keys[0]
        )
        st.session_state[
            selection_key
        ] = default_key

    selected_key = (
        st.session_state[
            selection_key
        ]
    )

    st.markdown(
        """
        <div class="vcg-section-heading">
            <div>
                <div class="vcg-section-kicker">DIGITAL TWIN WORKSPACE</div>
                <div class="vcg-section-title">Virtual Workshop</div>
            </div>
            <div class="vcg-live-pill">LIVE VEHICLE STATE</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(
        "The schematic is driven by the same component, build-plan and "
        "maintenance data as the rest of VCG. It is a system-level workshop "
        "map, not a claim of engineering-grade CAD geometry."
    )

    (
        installed_col,
        active_col,
        attention_col,
        systems_col,
    ) = st.columns(
        4
    )

    with installed_col:
        st.metric(
            "Installed components",
            snapshot[
                "installed_component_count"
            ],
            border=True,
        )

    with active_col:
        st.metric(
            "Active build changes",
            snapshot[
                "active_plan_count"
            ],
            border=True,
        )

    with attention_col:
        st.metric(
            "Maintenance attention",
            snapshot[
                "maintenance_attention_count"
            ],
            border=True,
        )

    with systems_col:
        st.metric(
            "Systems with activity",
            snapshot[
                "systems_with_activity"
            ],
            border=True,
        )

    system_names = {
        system[
            "system_key"
        ]: system[
            "name"
        ]
        for system in systems
    }

    selected_key = st.selectbox(
        "Inspect system",
        valid_keys,
        format_func=lambda key: (
            system_names[
                key
            ]
        ),
        key=selection_key,
        help=(
            "Choose a digital-twin system to inspect its current parts, "
            "planned changes, maintenance and evidence."
        ),
    )

    selected_system = snapshot[
        "system_lookup"
    ][
        selected_key
    ]

    blueprint_col, inspector_col = st.columns(
        [1.55, 1],
        gap="large",
        vertical_alignment="top",
    )

    with blueprint_col:
        st_components.html(
            workshop_blueprint_html(
                snapshot,
                selected_key,
            ),
            height=820,
            scrolling=False,
        )

    with inspector_col:
        st.markdown(
            f"### {selected_system['name']}"
        )

        st.caption(
            system_status_label(
                selected_system
            )
        )

        (
            installed_metric,
            planned_metric,
            maintenance_metric,
            history_metric,
        ) = st.columns(
            4
        )

        with installed_metric:
            st.metric(
                "Fitted",
                selected_system[
                    "installed_count"
                ],
                border=True,
            )

        with planned_metric:
            st.metric(
                "Planned",
                selected_system[
                    "planned_count"
                ],
                border=True,
            )

        with maintenance_metric:
            st.metric(
                "Open maint.",
                selected_system[
                    "maintenance_count"
                ],
                border=True,
            )

        with history_metric:
            st.metric(
                "History",
                selected_system[
                    "history_count"
                ],
                border=True,
            )

        if selected_system[
            "overdue_items"
        ]:
            st.error(
                f"{len(selected_system['overdue_items'])} linked maintenance "
                "item"
                f"{'' if len(selected_system['overdue_items']) == 1 else 's'} "
                "have reached a recorded due point."
            )
        elif selected_system[
            "due_soon_items"
        ]:
            st.warning(
                f"{len(selected_system['due_soon_items'])} linked maintenance "
                "item"
                f"{'' if len(selected_system['due_soon_items']) == 1 else 's'} "
                "are due soon."
            )

        (
            current_tab,
            plan_tab,
            maintenance_tab,
            evidence_tab,
        ) = st.tabs(
            [
                "Current",
                "Plan",
                "Maintenance",
                "Evidence",
            ]
        )

        with current_tab:
            if selected_system[
                "installed"
            ]:
                for component in selected_system[
                    "installed"
                ]:
                    st.markdown(
                        f"**{component['name']}**"
                    )

                    meta = [
                        "Installed"
                    ]

                    if component.get(
                        "manufacturer"
                    ):
                        meta.append(
                            str(
                                component[
                                    "manufacturer"
                                ]
                            )
                        )

                    if component.get(
                        "part_number"
                    ):
                        meta.append(
                            str(
                                component[
                                    "part_number"
                                ]
                            )
                        )

                    if component.get(
                        "weight_kg"
                    ) is not None:
                        meta.append(
                            f"{float(component['weight_kg']):.1f} kg"
                        )

                    st.caption(
                        " · ".join(
                            meta
                        )
                    )

                    if component.get(
                        "notes"
                    ):
                        st.write(
                            component[
                                "notes"
                            ]
                        )

                    st.divider()
            else:
                st.caption(
                    "No fitted structured components are recorded in this system."
                )

            if selected_system[
                "removed"
            ]:
                with st.expander(
                    "Removed component history"
                ):
                    for component in selected_system[
                        "removed"
                    ]:
                        st.markdown(
                            f"**{component['name']}**"
                        )

                        removed_at = component.get(
                            "removed_at"
                        )
                        removed_mileage = component.get(
                            "removed_mileage"
                        )

                        details = []

                        if removed_at:
                            details.append(
                                str(
                                    removed_at
                                )
                            )

                        if removed_mileage is not None:
                            details.append(
                                f"{int(removed_mileage):,} mi"
                            )

                        if details:
                            st.caption(
                                " · ".join(
                                    details
                                )
                            )

        with plan_tab:
            if selected_system[
                "active_plans"
            ]:
                for item in selected_system[
                    "active_plans"
                ]:
                    component_name = _component_name(
                        item.get(
                            "component_id"
                        ),
                        snapshot[
                            "component_lookup"
                        ],
                    )

                    action = (
                        "Install"
                        if item.get(
                            "action"
                        )
                        == "install"
                        else "Remove"
                    )

                    st.markdown(
                        f"**{action}: {component_name}**"
                    )

                    meta = [
                        str(
                            item.get(
                                "status",
                                "planned",
                            )
                        ).title(),
                        str(
                            item.get(
                                "priority",
                                "normal",
                            )
                        ).title(),
                    ]

                    if item.get(
                        "estimated_cost_gbp"
                    ) is not None:
                        meta.append(
                            f"£{float(item['estimated_cost_gbp']):,.2f}"
                        )

                    if (
                        item.get(
                            "action"
                        )
                        == "install"
                    ):
                        meta.append(
                            "Compatibility "
                            + str(
                                item.get(
                                    "compatibility_status",
                                    "unknown",
                                )
                            ).replace(
                                "_",
                                " ",
                            ).title()
                        )

                    st.caption(
                        " · ".join(
                            meta
                        )
                    )

                    if item.get(
                        "compatibility_notes"
                    ):
                        st.caption(
                            "Compatibility: "
                            + str(
                                item[
                                    "compatibility_notes"
                                ]
                            )
                        )

                    if item.get(
                        "notes"
                    ):
                        st.write(
                            item[
                                "notes"
                            ]
                        )

                    st.divider()
            else:
                st.caption(
                    "No active install/removal plans affect this system."
                )

            st.button(
                "Open Build Planner",
                key=(
                    "workshop_open_build_planner_"
                    f"{vehicle['id']}_"
                    f"{selected_key}"
                ),
                type="primary",
                width="stretch",
                on_click=_switch_workspace,
                args=(
                    workspace_state_key,
                    "Build Planner",
                ),
            )

        with maintenance_tab:
            if selected_system[
                "maintenance_items"
            ]:
                for item in selected_system[
                    "maintenance_items"
                ]:
                    st.markdown(
                        f"**{item['title']}**"
                    )

                    if maintenance_is_overdue(
                        item,
                        current_mileage,
                    ):
                        attention = "OVERDUE"
                    elif maintenance_is_due_soon(
                        item,
                        current_mileage,
                    ):
                        attention = "DUE SOON"
                    else:
                        attention = str(
                            item.get(
                                "priority",
                                "normal",
                            )
                        ).upper()

                    st.caption(
                        f"{attention} · "
                        f"{maintenance_due_label(item)}"
                    )

                    if item.get(
                        "notes"
                    ):
                        st.write(
                            item[
                                "notes"
                            ]
                        )

                    st.divider()
            else:
                st.caption(
                    "No open maintenance is linked to this system."
                )

            if selected_system[
                "maintenance_history"
            ]:
                with st.expander(
                    "Service history"
                ):
                    for record in selected_system[
                        "maintenance_history"
                    ][
                        :8
                    ]:
                        st.markdown(
                            f"**{record['title']}**"
                        )

                        meta = [
                            str(
                                record.get(
                                    "performed_at",
                                    "Unknown date",
                                )
                            )
                        ]

                        if record.get(
                            "performed_mileage"
                        ) is not None:
                            meta.append(
                                f"{int(record['performed_mileage']):,} mi"
                            )

                        if record.get(
                            "cost_gbp"
                        ) is not None:
                            meta.append(
                                f"£{float(record['cost_gbp']):,.2f}"
                            )

                        st.caption(
                            " · ".join(
                                meta
                            )
                        )

            st.button(
                "Open Maintenance OS",
                key=(
                    "workshop_open_maintenance_"
                    f"{vehicle['id']}_"
                    f"{selected_key}"
                ),
                width="stretch",
                on_click=_switch_workspace,
                args=(
                    workspace_state_key,
                    "Maintenance OS",
                ),
            )

        with evidence_tab:
            if selected_system[
                "verified_specs"
            ]:
                for spec in selected_system[
                    "verified_specs"
                ]:
                    value = (
                        spec.get(
                            "value_text"
                        )
                        if spec.get(
                            "value_text"
                        )
                        is not None
                        else spec.get(
                            "value_numeric"
                        )
                    )

                    unit = (
                        f" {spec['unit']}"
                        if spec.get(
                            "unit"
                        )
                        else ""
                    )

                    st.markdown(
                        f"**{spec['label']}**"
                    )
                    st.caption(
                        f"{value}{unit} · VERIFIED"
                    )

                    if spec.get(
                        "source_reference"
                    ):
                        st.caption(
                            "Source: "
                            + str(
                                spec[
                                    "source_reference"
                                ]
                            )
                        )

                    st.divider()
            else:
                st.caption(
                    "No component-linked verified specifications are "
                    "recorded for this system yet."
                )

            if selected_system[
                "known_installed_weight_kg"
            ]:
                st.metric(
                    "Known installed component weight",
                    (
                        f"{selected_system['known_installed_weight_kg']:.1f} kg"
                    ),
                    border=True,
                )

        st.markdown(
            "#### Workshop navigation"
        )

        nav_a, nav_b = st.columns(
            2
        )

        with nav_a:
            st.button(
                "Garage AI",
                key=(
                    "workshop_open_ai_"
                    f"{vehicle['id']}"
                ),
                width="stretch",
                on_click=_switch_workspace,
                args=(
                    workspace_state_key,
                    "Garage AI",
                ),
            )

        with nav_b:
            st.button(
                "Build Planner",
                key=(
                    "workshop_open_plan_"
                    f"{vehicle['id']}"
                ),
                width="stretch",
                on_click=_switch_workspace,
                args=(
                    workspace_state_key,
                    "Build Planner",
                ),
            )
