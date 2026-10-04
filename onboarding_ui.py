from __future__ import annotations

import streamlit as st

from vehicle_intake_ui import (
    render_new_vehicle_intake_form,
)


def render_first_run_onboarding(
    client,
    owner_id: str,
) -> dict | None:
    """Render the focused zero-vehicle V0 onboarding experience."""

    st.markdown(
        """
        <div class="vcg-first-run-shell">
            <div class="vcg-first-run-kicker">WELCOME TO VCG</div>
            <div class="vcg-first-run-title">
                Your garage starts with one real car.
            </div>
            <div class="vcg-first-run-copy">
                Create your first Virtual Twin. Start with the basics now,
                then improve it over time with photos, modifications,
                documents and evidence.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    step_a, step_b, step_c = st.columns(
        3,
        gap="small",
    )

    with step_a:
        st.markdown(
            """
            <div class="vcg-first-run-step">
                <span>01</span>
                <strong>Add your car</strong>
                <small>Identity, engine and mileage.</small>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with step_b:
        st.markdown(
            """
            <div class="vcg-first-run-step">
                <span>02</span>
                <strong>Build the Twin</strong>
                <small>Add photos, mods and evidence when ready.</small>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with step_c:
        st.markdown(
            """
            <div class="vcg-first-run-step">
                <span>03</span>
                <strong>Use your garage</strong>
                <small>AI, maintenance, diagnostics and sharing.</small>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        "### Create your first Twin"
    )
    st.caption(
        "You only need the basics to begin. Registration and VIN are optional."
    )

    return render_new_vehicle_intake_form(
        client=client,
        owner_id=owner_id,
    )
