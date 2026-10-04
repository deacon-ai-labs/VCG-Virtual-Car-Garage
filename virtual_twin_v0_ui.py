from __future__ import annotations

from html import escape

import streamlit as st


TWIN_ACTIONS = (
    (
        "⌕",
        "Inspect",
        "Virtual Workshop",
    ),
    (
        "◉",
        "Maintain",
        "Maintenance OS",
    ),
    (
        "△",
        "Diagnose",
        "Diagnostics",
    ),
    (
        "＋",
        "Modify",
        "Build Planner",
    ),
    (
        "✦",
        "AI",
        "Garage AI",
    ),
)


def _open_workspace(
    workspace_state_key: str,
    workspace_name: str,
) -> None:
    st.session_state[
        workspace_state_key
    ] = workspace_name


def render_virtual_twin_v0(
    vehicle: dict,
    photo_url: str | None,
    snapshot: dict,
    workspace_state_key: str,
    contextual_badges: dict[str, int],
) -> None:
    """Render the simple car-first V0 Virtual Twin."""

    profile_name = escape(
        str(
            vehicle.get(
                "profile_name",
                "My Car",
            )
        )
    )
    manufacturer = escape(
        str(
            vehicle.get(
                "manufacturer",
                ""
            )
        )
    )
    model = escape(
        str(
            vehicle.get(
                "model",
                ""
            )
        )
    )
    engine = escape(
        str(
            vehicle.get(
                "engine",
                ""
            )
        )
    )

    st.markdown(
        f"""
        <div class="vcg-twin-heading">
            <div>
                <div class="vcg-section-kicker">VIRTUAL TWIN</div>
                <div class="vcg-twin-profile">{profile_name}</div>
                <div class="vcg-twin-identity">
                    {vehicle.get('year', '')} {manufacturer} {model}
                </div>
                <div class="vcg-twin-engine">{engine}</div>
            </div>
            <div class="vcg-owned-pill">● OWNED TWIN</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container(
        key="vcg_twin_hero"
    ):
        if photo_url:
            st.image(
                photo_url,
                width="stretch",
            )
        else:
            st.markdown(
                """
                <div class="vcg-twin-placeholder">
                    <span>🚘</span>
                    <strong>Add a photo of your car</strong>
                    <small>Your real vehicle is the centre of the Twin.</small>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with st.container(
        key="vcg_twin_stats"
    ):
        (
            mileage_col,
            fitted_col,
            maintenance_col,
            diagnostic_col,
        ) = st.columns(
            4
        )

        with mileage_col:
            st.metric(
                "Mileage",
                f"{snapshot['mileage']:,}",
                border=True,
            )

        with fitted_col:
            st.metric(
                "Fitted",
                snapshot[
                    "installed_count"
                ],
                border=True,
            )

        with maintenance_col:
            st.metric(
                "Maintenance",
                snapshot[
                    "maintenance_state"
                ],
                border=True,
            )

        with diagnostic_col:
            st.metric(
                "Diagnostics",
                snapshot[
                    "active_case_count"
                ],
                border=True,
            )

    with st.container(
        key="vcg_twin_actions"
    ):
        action_columns = st.columns(
            len(
                TWIN_ACTIONS
            ),
            gap="small",
        )

        for column, (
            icon,
            label,
            workspace,
        ) in zip(
            action_columns,
            TWIN_ACTIONS,
        ):
            with column:
                badge = int(
                    contextual_badges.get(
                        workspace,
                        0,
                    )
                    or 0
                )

                button_label = (
                    f"{icon} {label}"
                )

                if badge:
                    button_label += (
                        f" · {badge}"
                    )

                st.button(
                    button_label,
                    key=(
                        "twin_action_"
                        + workspace.lower().replace(
                            " ",
                            "_",
                        )
                    ),
                    width="stretch",
                    on_click=_open_workspace,
                    args=(
                        workspace_state_key,
                        workspace,
                    ),
                )

    if (
        snapshot[
            "active_plan_count"
        ]
        or snapshot[
            "maintenance_state"
        ]
        not in {
            "Clear",
            "Unknown",
        }
        or snapshot[
            "active_case_count"
        ]
    ):
        status_parts = []

        if snapshot[
            "active_plan_count"
        ]:
            status_parts.append(
                f"{snapshot['active_plan_count']} planned build change"
                f"{'' if snapshot['active_plan_count'] == 1 else 's'}"
            )

        if snapshot[
            "maintenance_state"
        ] not in {
            "Clear",
            "Unknown",
        }:
            status_parts.append(
                (
                    "maintenance "
                    + str(
                        snapshot[
                            "maintenance_state"
                        ]
                    ).lower()
                )
            )

        if snapshot[
            "active_case_count"
        ]:
            status_parts.append(
                f"{snapshot['active_case_count']} active diagnostic case"
                f"{'' if snapshot['active_case_count'] == 1 else 's'}"
            )

        st.caption(
            " · ".join(
                status_parts
            )
        )

    if snapshot[
        "recent_activity"
    ]:
        st.markdown(
            "#### Recent activity"
        )

        for item in snapshot[
            "recent_activity"
        ]:
            st.markdown(
                f"**{item['title']}**"
            )
            st.caption(
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

    with st.expander(
        "Twin details"
    ):
        st.caption(
            f"{snapshot['mapped_component_count']} mapped components · "
            f"{snapshot['verified_spec_count']} verified specs"
        )

        installed = snapshot[
            "installed_preview"
        ]

        if installed:
            st.markdown(
                "**Current recorded build**"
            )

            for component in installed:
                st.caption(
                    "• "
                    + str(
                        component.get(
                            "name",
                            "Unnamed component",
                        )
                    )
                )
        else:
            st.caption(
                "No structured fitted modifications are recorded yet."
            )
