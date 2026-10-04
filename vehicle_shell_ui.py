from __future__ import annotations

from html import escape

import streamlit as st


def render_vehicle_command_deck(
    vehicle: dict,
    photo_url: str | None,
    maintenance: dict,
    diagnostics: dict,
    build_plan: dict,
    structured_build: dict,
) -> None:
    """Render a compact active-vehicle identity and status deck."""

    photo_col, identity_col = st.columns(
        [1.35, 6.65],
        gap="medium",
        vertical_alignment="center",
    )

    with photo_col:
        with st.container(
            key="vcg_command_photo"
        ):
            if photo_url:
                st.image(
                    photo_url,
                    width="stretch",
                )
            else:
                st.markdown(
                    """
                    <div class="vcg-photo-placeholder vcg-command-photo-placeholder">
                        <span>🚘</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    profile_name = escape(
        str(
            vehicle.get(
                "profile_name",
                "Vehicle",
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

    active_cases = int(
        diagnostics.get(
            "active_case_count",
            0,
        )
        or 0
    )
    active_changes = int(
        build_plan.get(
            "active_count",
            0,
        )
        or 0
    )
    installed = int(
        structured_build.get(
            "installed_count",
            0,
        )
        or 0
    )

    with identity_col:
        st.markdown(
            f"""
            <div class="vcg-command-deck">
                <div class="vcg-command-heading">
                    <div>
                        <div class="vcg-command-profile">{profile_name}</div>
                        <div class="vcg-command-title">
                            {vehicle.get('year', '')} {manufacturer} {model}
                        </div>
                        <div class="vcg-command-subtitle">{engine}</div>
                    </div>
                    <div class="vcg-live-pill">ACTIVE VEHICLE</div>
                </div>
                <div class="vcg-command-grid">
                    <div class="vcg-command-stat">
                        <span>MILEAGE</span>
                        <strong>{int(vehicle.get('mileage') or 0):,} mi</strong>
                    </div>
                    <div class="vcg-command-stat">
                        <span>MAINTENANCE</span>
                        <strong>{escape(str(maintenance.get('state', 'Unknown')))}</strong>
                        <small>{escape(str(maintenance.get('detail', '')))}</small>
                    </div>
                    <div class="vcg-command-stat">
                        <span>DIAGNOSTICS</span>
                        <strong>{active_cases} active</strong>
                    </div>
                    <div class="vcg-command-stat">
                        <span>BUILD</span>
                        <strong>{installed} fitted</strong>
                        <small>{active_changes} planned</small>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
