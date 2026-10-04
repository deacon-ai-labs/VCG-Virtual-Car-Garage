from __future__ import annotations

import streamlit as st


def _switch_workspace(
    workspace_state_key: str,
    workspace_name: str,
) -> None:
    st.session_state[
        workspace_state_key
    ] = workspace_name


def _render_attention(
    item: dict,
) -> None:
    message = (
        f"**{item['title']}** — "
        f"{item['detail']}"
    )

    severity = item.get(
        "severity"
    )

    if severity == "error":
        st.error(
            message
        )
    elif severity == "warning":
        st.warning(
            message
        )
    elif severity == "success":
        st.success(
            message
        )
    else:
        st.info(
            message
        )


def render_vehicle_home(
    vehicle: dict,
    snapshot: dict,
    structured_build: dict,
    maintenance: dict,
    workspace_state_key: str,
) -> None:
    """Render the M20 vehicle landing workspace."""

    st.markdown(
        """
        <div class="vcg-home-hero">
            <div>
                <div class="vcg-section-kicker">VEHICLE OPERATING SYSTEM</div>
                <div class="vcg-home-title">Vehicle Home</div>
                <div class="vcg-home-subtitle">
                    Current state, attention and recent recorded activity.
                </div>
            </div>
            <div class="vcg-live-pill">LIVE VEHICLE RECORD</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    (
        maintenance_col,
        diagnostics_col,
        build_col,
        twin_col,
    ) = st.columns(
        4
    )

    with maintenance_col:
        st.metric(
            "Maintenance",
            snapshot[
                "maintenance_state"
            ],
            border=True,
        )
        st.caption(
            snapshot[
                "maintenance_detail"
            ]
        )

    with diagnostics_col:
        st.metric(
            "Diagnostics",
            snapshot[
                "active_case_count"
            ],
            border=True,
        )
        st.caption(
            "Active cases"
        )

    with build_col:
        st.metric(
            "Build plan",
            snapshot[
                "planned_change_count"
            ],
            border=True,
        )
        st.caption(
            "Active changes"
        )

    with twin_col:
        st.metric(
            "Digital twin",
            snapshot[
                "mapped_component_count"
            ],
            border=True,
        )
        st.caption(
            "Mapped components"
        )

    attention_col, actions_col = st.columns(
        [1.7, 1],
        gap="large",
    )

    with attention_col:
        st.markdown(
            "### Needs attention"
        )

        for item in snapshot[
            "attention"
        ]:
            _render_attention(
                item
            )

    with actions_col:
        st.markdown(
            "### Quick actions"
        )

        action_rows = (
            (
                "✦ Ask Garage AI",
                "Garage AI",
            ),
            (
                "◇ Open virtual workshop",
                "Virtual Workshop",
            ),
            (
                "△ Open diagnostics",
                "Diagnostics",
            ),
            (
                "◉ Review maintenance",
                "Maintenance OS",
            ),
            (
                "＋ Open build planner",
                "Build Planner",
            ),
        )

        for label, workspace in action_rows:
            st.button(
                label,
                key=(
                    "vehicle_home_action_"
                    + workspace.lower().replace(
                        " ",
                        "_",
                    )
                ),
                width="stretch",
                on_click=_switch_workspace,
                args=(
                    workspace_state_key,
                    workspace,
                ),
            )

    st.divider()

    build_col, activity_col = st.columns(
        [1.15, 1],
        gap="large",
    )

    with build_col:
        st.markdown(
            "### Current configuration"
        )

        installed = structured_build.get(
            "installed",
            []
        )

        if installed:
            for component in installed[:8]:
                st.markdown(
                    f"**{component['name']}**"
                )
                st.caption(
                    str(
                        component.get(
                            "system_key",
                            "Other",
                        )
                    ).replace(
                        "_",
                        " ",
                    ).title()
                )
        else:
            st.caption(
                "No installed structured components are recorded."
            )

        if len(
            installed
        ) > 8:
            st.caption(
                f"+ {len(installed) - 8} more installed components"
            )

    with activity_col:
        st.markdown(
            "### Recent recorded activity"
        )

        if snapshot[
            "recent_activity"
        ]:
            for item in snapshot[
                "recent_activity"
            ]:
                st.markdown(
                    f"**{item['title']}**"
                )
                st.caption(
                    (
                        item[
                            "detail"
                        ]
                        + (
                            f" · {item['timestamp'][:10]}"
                            if item[
                                "timestamp"
                            ]
                            else ""
                        )
                    )
                )
        else:
            st.caption(
                "No service or component lifecycle activity is recorded yet."
            )

    st.divider()

    st.markdown(
        "### Digital-twin coverage"
    )

    (
        systems_col,
        mapped_col,
        specs_col,
        events_col,
    ) = st.columns(
        4
    )

    with systems_col:
        st.metric(
            "Vehicle systems",
            snapshot[
                "system_count"
            ],
            border=True,
        )

    with mapped_col:
        st.metric(
            "Mapped components",
            snapshot[
                "mapped_component_count"
            ],
            border=True,
        )

    with specs_col:
        st.metric(
            "Verified specs",
            snapshot[
                "verified_spec_count"
            ],
            border=True,
        )

    with events_col:
        st.metric(
            "Lifecycle events",
            snapshot[
                "lifecycle_event_count"
            ],
            border=True,
        )

    if maintenance.get(
        "history_count",
        0,
    ):
        st.caption(
            f"{snapshot['service_history_count']} service-history "
            "record"
            f"{'' if snapshot['service_history_count'] == 1 else 's'} "
            "are linked to this vehicle."
        )
