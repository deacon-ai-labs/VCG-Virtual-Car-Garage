from __future__ import annotations

from datetime import date, datetime, time, timezone

import streamlit as st

from database import (
    add_diagnostic_case,
    add_diagnostic_check,
    add_diagnostic_hypothesis,
    delete_diagnostic_case,
    delete_diagnostic_check,
    delete_diagnostic_hypothesis,
    update_diagnostic_case,
    update_diagnostic_check,
    update_diagnostic_hypothesis,
)
from diagnostics import (
    case_snapshot,
    diagnostic_vehicle_snapshot,
)


CASE_STATUSES = [
    "open",
    "monitoring",
    "resolved",
    "closed",
]

CASE_PRIORITIES = [
    "low",
    "normal",
    "high",
    "critical",
]

DRIVE_RISKS = [
    "unknown",
    "safe_with_caution",
    "avoid_driving",
    "do_not_drive",
]

HYPOTHESIS_STATUSES = [
    "possible",
    "leading",
    "weakened",
    "ruled_out",
    "confirmed",
]

HYPOTHESIS_SOURCES = [
    "user",
    "garage_ai",
    "mechanic",
    "test_result",
    "other",
]

CHECK_TYPES = [
    "observation",
    "inspection",
    "measurement",
    "scan",
    "mechanical_test",
    "test_drive",
    "other",
]

CHECK_OUTCOMES = [
    "supports",
    "weakens",
    "neutral",
    "inconclusive",
]


def _pretty(
    value: str,
) -> str:
    return value.replace(
        "_",
        " ",
    ).title()


def _optional_mileage(
    value: str,
) -> int | None:
    clean = value.strip()

    if not clean:
        return None

    try:
        parsed = int(
            clean
        )
    except ValueError as error:
        raise ValueError(
            "Mileage must be a whole number."
        ) from error

    if parsed < 0:
        raise ValueError(
            "Mileage cannot be negative."
        )

    return parsed


def _date_to_timestamptz(
    value: date,
) -> str:
    return datetime.combine(
        value,
        time(
            hour=12,
        ),
        tzinfo=timezone.utc,
    ).isoformat()


def _component_options(
    components: list[dict],
) -> tuple[list[str], dict[str, str]]:
    visible = [
        component
        for component in components
        if component.get(
            "lifecycle_status"
        )
        != "cancelled"
    ]

    system_names = {
        component.get(
            "system_key"
        ): component.get(
            "name"
        )
        for component in visible
        if component.get(
            "component_type"
        )
        == "system"
    }

    ordered = sorted(
        visible,
        key=lambda component: (
            component.get(
                "sort_order",
                0,
            ),
            component.get(
                "system_key",
                "",
            ),
            component.get(
                "name",
                "",
            ),
        ),
    )

    options = [
        ""
    ]
    labels = {
        "": "Vehicle-level / not linked",
    }

    for component in ordered:
        component_id = str(
            component[
                "id"
            ]
        )

        options.append(
            component_id
        )

        name = component.get(
            "name",
            "Unnamed component",
        )

        if component.get(
            "component_type"
        ) == "system":
            labels[
                component_id
            ] = (
                f"System · {name}"
            )
        else:
            system_name = (
                system_names.get(
                    component.get(
                        "system_key"
                    )
                )
                or component.get(
                    "system_key"
                )
                or "Other"
            )

            labels[
                component_id
            ] = (
                f"{system_name} · {name}"
            )

    return (
        options,
        labels,
    )


def _component_name_lookup(
    components: list[dict],
) -> dict[str, str]:
    return {
        str(
            component[
                "id"
            ]
        ): component.get(
            "name",
            "Unnamed component",
        )
        for component in components
    }


def _switch_workspace(
    workspace_state_key: str,
    workspace_name: str,
) -> None:
    st.session_state[
        workspace_state_key
    ] = workspace_name


def _render_create_case(
    client,
    owner_id: str,
    vehicle: dict,
) -> None:
    with st.form(
        "diagnostic_create_case",
        clear_on_submit=True,
    ):
        title = st.text_input(
            "Case title",
            placeholder="e.g. Pulls left under braking",
        )
        symptom = st.text_area(
            "Symptom",
            placeholder=(
                "Describe exactly what the car does, not what you think causes it."
            ),
        )
        priority = st.selectbox(
            "Priority",
            CASE_PRIORITIES,
            index=1,
        )
        drive_risk = st.selectbox(
            "Current drive-risk assessment",
            DRIVE_RISKS,
            index=0,
            format_func=_pretty,
        )
        onset_date = st.date_input(
            "Approximate onset date",
            value=None,
        )
        onset_mileage = st.text_input(
            "Approximate onset mileage",
            placeholder="Optional",
        )
        conditions = st.text_area(
            "Operating conditions",
            placeholder=(
                "When does it happen? Speed, braking, temperature, load, "
                "cold/hot engine, road surface, etc."
            ),
        )

        submitted = st.form_submit_button(
            "Create diagnostic case",
            type="primary",
            width="stretch",
        )

    if submitted:
        if not title.strip():
            st.warning(
                "Enter a concise case title."
            )
            return

        if not symptom.strip():
            st.warning(
                "Describe the symptom before creating the case."
            )
            return

        try:
            saved = add_diagnostic_case(
                client,
                owner_id,
                vehicle[
                    "id"
                ],
                {
                    "title": title.strip(),
                    "symptom_description": symptom.strip(),
                    "priority": priority,
                    "drive_risk": drive_risk,
                    "onset_date": (
                        onset_date.isoformat()
                        if onset_date
                        else None
                    ),
                    "onset_mileage": _optional_mileage(
                        onset_mileage
                    ),
                    "operating_conditions": (
                        conditions.strip()
                        or None
                    ),
                },
            )
        except ValueError as error:
            st.warning(
                str(
                    error
                )
            )
        except Exception as error:
            st.error(
                "VCG could not create the diagnostic case."
            )
            st.exception(
                error
            )
        else:
            st.session_state[
                "diagnostic_case_focus_"
                f"{vehicle['id']}"
            ] = saved[
                "id"
            ]
            st.rerun()


def render_diagnostics_workspace(
    client,
    owner_id: str,
    vehicle: dict,
    components: list[dict],
    cases: list[dict],
    hypotheses: list[dict],
    checks: list[dict],
    workspace_state_key: str,
) -> None:
    """Render the structured M19 diagnostic investigation workspace."""

    vehicle_snapshot = (
        diagnostic_vehicle_snapshot(
            cases,
            hypotheses,
            checks,
        )
    )

    component_options, component_labels = (
        _component_options(
            components
        )
    )
    component_names = (
        _component_name_lookup(
            components
        )
    )

    st.markdown(
        """
        <div class="vcg-section-heading">
            <div>
                <div class="vcg-section-kicker">EVIDENCE-LED TROUBLESHOOTING</div>
                <div class="vcg-section-title">Diagnostics</div>
            </div>
            <div class="vcg-live-pill">CASE WORKSPACE</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(
        "A hypothesis is not a diagnosis. VCG keeps suspected causes, "
        "completed checks and recorded findings as separate evidence."
    )

    (
        active_col,
        resolved_col,
        open_checks_col,
        evidence_col,
    ) = st.columns(
        4
    )

    with active_col:
        st.metric(
            "Active cases",
            vehicle_snapshot[
                "active_case_count"
            ],
            border=True,
        )

    with resolved_col:
        st.metric(
            "Resolved / closed",
            vehicle_snapshot[
                "resolved_case_count"
            ],
            border=True,
        )

    with open_checks_col:
        st.metric(
            "Planned checks",
            vehicle_snapshot[
                "open_check_count"
            ],
            border=True,
        )

    with evidence_col:
        st.metric(
            "Completed checks",
            vehicle_snapshot[
                "completed_check_count"
            ],
            border=True,
        )

    with st.expander(
        "＋ New diagnostic case",
        expanded=(
            not cases
        ),
    ):
        _render_create_case(
            client,
            owner_id,
            vehicle,
        )

    if not cases:
        st.info(
            "Create the first diagnostic case to begin a structured investigation."
        )
        return

    focus_key = (
        "diagnostic_case_focus_"
        f"{vehicle['id']}"
    )

    case_ids = [
        str(
            case[
                "id"
            ]
        )
        for case in cases
    ]

    case_lookup = {
        str(
            case[
                "id"
            ]
        ): case
        for case in cases
    }

    if (
        focus_key
        not in st.session_state
        or str(
            st.session_state[
                focus_key
            ]
        )
        not in case_lookup
    ):
        st.session_state[
            focus_key
        ] = case_ids[0]

    selected_case_id = st.selectbox(
        "Diagnostic case",
        case_ids,
        key=focus_key,
        format_func=lambda case_id: (
            (
                "● "
                if case_lookup[
                    case_id
                ].get(
                    "status"
                )
                in {
                    "open",
                    "monitoring",
                }
                else "✓ "
            )
            + case_lookup[
                case_id
            ].get(
                "title",
                "Untitled case",
            )
        ),
    )

    selected_case = case_lookup[
        selected_case_id
    ]

    snapshot = case_snapshot(
        selected_case,
        hypotheses,
        checks,
    )

    st.markdown(
        f"### {selected_case['title']}"
    )

    status_line = (
        f"{_pretty(selected_case.get('status', 'open'))}"
        f" · {_pretty(selected_case.get('priority', 'normal'))} priority"
        f" · Drive risk: {_pretty(selected_case.get('drive_risk', 'unknown'))}"
    )

    st.caption(
        status_line
    )

    if selected_case.get(
        "drive_risk"
    ) == "do_not_drive":
        st.error(
            "This case is recorded as DO NOT DRIVE."
        )
    elif selected_case.get(
        "drive_risk"
    ) == "avoid_driving":
        st.warning(
            "This case is recorded as avoid driving until investigated."
        )

    (
        hypothesis_metric,
        planned_metric,
        evidence_metric,
        confirmed_metric,
    ) = st.columns(
        4
    )

    with hypothesis_metric:
        st.metric(
            "Hypotheses",
            snapshot[
                "hypothesis_count"
            ],
            border=True,
        )

    with planned_metric:
        st.metric(
            "Planned checks",
            snapshot[
                "planned_check_count"
            ],
            border=True,
        )

    with evidence_metric:
        st.metric(
            "Completed evidence",
            snapshot[
                "evidence_count"
            ],
            border=True,
        )

    with confirmed_metric:
        st.metric(
            "Confirmed",
            snapshot[
                "hypothesis_counts"
            ][
                "confirmed"
            ],
            border=True,
        )

    if snapshot[
        "next_check"
    ]:
        next_check = snapshot[
            "next_check"
        ]

        st.info(
            "**Next recorded check:** "
            + str(
                next_check.get(
                    "title",
                    "Untitled check",
                )
            )
            + (
                " — "
                + str(
                    next_check[
                        "procedure"
                    ]
                )
                if next_check.get(
                    "procedure"
                )
                else ""
            )
        )

    (
        overview_tab,
        hypotheses_tab,
        checks_tab,
        resolution_tab,
    ) = st.tabs(
        [
            "Case",
            "Hypotheses",
            "Checks & evidence",
            "Resolution",
        ]
    )

    with overview_tab:
        st.markdown(
            "#### Recorded symptom"
        )
        st.write(
            selected_case[
                "symptom_description"
            ]
        )

        if selected_case.get(
            "operating_conditions"
        ):
            st.markdown(
                "#### Conditions"
            )
            st.write(
                selected_case[
                    "operating_conditions"
                ]
            )

        onset = []

        if selected_case.get(
            "onset_date"
        ):
            onset.append(
                str(
                    selected_case[
                        "onset_date"
                    ]
                )
            )

        if selected_case.get(
            "onset_mileage"
        ) is not None:
            onset.append(
                f"{int(selected_case['onset_mileage']):,} mi"
            )

        if onset:
            st.caption(
                "Onset: "
                + " · ".join(
                    onset
                )
            )

        with st.expander(
            "Edit case record"
        ):
            with st.form(
                f"diagnostic_edit_case_{selected_case_id}"
            ):
                edit_title = st.text_input(
                    "Case title",
                    value=selected_case[
                        "title"
                    ],
                )
                edit_symptom = st.text_area(
                    "Symptom",
                    value=selected_case[
                        "symptom_description"
                    ],
                )
                if selected_case.get(
                    "status"
                ) in {
                    "open",
                    "monitoring",
                }:
                    edit_case_status = st.selectbox(
                        "Investigation state",
                        [
                            "open",
                            "monitoring",
                        ],
                        index=(
                            0
                            if selected_case.get(
                                "status"
                            )
                            == "open"
                            else 1
                        ),
                        format_func=_pretty,
                    )
                else:
                    edit_case_status = selected_case.get(
                        "status",
                        "open",
                    )

                edit_priority = st.selectbox(
                    "Priority",
                    CASE_PRIORITIES,
                    index=CASE_PRIORITIES.index(
                        selected_case.get(
                            "priority",
                            "normal",
                        )
                    ),
                )
                edit_drive_risk = st.selectbox(
                    "Drive-risk assessment",
                    DRIVE_RISKS,
                    index=DRIVE_RISKS.index(
                        selected_case.get(
                            "drive_risk",
                            "unknown",
                        )
                    ),
                    format_func=_pretty,
                )
                edit_onset_date = st.date_input(
                    "Approximate onset date",
                    value=(
                        date.fromisoformat(
                            str(
                                selected_case[
                                    "onset_date"
                                ]
                            )[:10]
                        )
                        if selected_case.get(
                            "onset_date"
                        )
                        else None
                    ),
                )
                edit_onset_mileage = st.text_input(
                    "Approximate onset mileage",
                    value=(
                        str(
                            selected_case[
                                "onset_mileage"
                            ]
                        )
                        if selected_case.get(
                            "onset_mileage"
                        )
                        is not None
                        else ""
                    ),
                )
                edit_conditions = st.text_area(
                    "Operating conditions",
                    value=(
                        selected_case.get(
                            "operating_conditions"
                        )
                        or ""
                    ),
                )

                save_case = st.form_submit_button(
                    "Save case",
                    width="stretch",
                )

            if save_case:
                if not edit_title.strip():
                    st.warning(
                        "Case title cannot be blank."
                    )
                elif not edit_symptom.strip():
                    st.warning(
                        "Symptom cannot be blank."
                    )
                else:
                    try:
                        update_diagnostic_case(
                            client,
                            selected_case_id,
                            {
                                "title": edit_title.strip(),
                                "symptom_description": edit_symptom.strip(),
                                "status": edit_case_status,
                                "priority": edit_priority,
                                "drive_risk": edit_drive_risk,
                                "onset_date": (
                                    edit_onset_date.isoformat()
                                    if edit_onset_date
                                    else None
                                ),
                                "onset_mileage": _optional_mileage(
                                    edit_onset_mileage
                                ),
                                "operating_conditions": (
                                    edit_conditions.strip()
                                    or None
                                ),
                            },
                        )
                    except ValueError as error:
                        st.warning(
                            str(
                                error
                            )
                        )
                    except Exception as error:
                        st.error(
                            "VCG could not update the diagnostic case."
                        )
                        st.exception(
                            error
                        )
                    else:
                        st.rerun()

        if st.button(
            "Discuss this investigation in Garage AI",
            key=(
                "diagnostic_open_ai_"
                f"{selected_case_id}"
            ),
            type="primary",
            width="stretch",
            on_click=_switch_workspace,
            args=(
                workspace_state_key,
                "Garage AI",
            ),
        ):
            pass

    with hypotheses_tab:
        case_hypotheses = snapshot[
            "hypotheses"
        ]

        if not case_hypotheses:
            st.caption(
                "No candidate causes have been recorded yet."
            )

        for hypothesis in case_hypotheses:
            component_name = (
                component_names.get(
                    str(
                        hypothesis.get(
                            "component_id"
                        )
                    )
                )
                if hypothesis.get(
                    "component_id"
                )
                else "Vehicle-level"
            )

            st.markdown(
                f"### {hypothesis['title']}"
            )

            st.caption(
                f"{_pretty(hypothesis.get('status', 'possible'))}"
                f" · {component_name}"
                f" · Source: {_pretty(hypothesis.get('source_kind', 'user'))}"
            )

            if hypothesis.get(
                "rationale"
            ):
                st.write(
                    hypothesis[
                        "rationale"
                    ]
                )

            linked_checks = [
                check
                for check in snapshot[
                    "checks"
                ]
                if str(
                    check.get(
                        "hypothesis_id"
                    )
                )
                == str(
                    hypothesis[
                        "id"
                    ]
                )
            ]

            if linked_checks:
                completed_linked = sum(
                    1
                    for check in linked_checks
                    if check.get(
                        "status"
                    )
                    == "completed"
                )

                st.caption(
                    f"{len(linked_checks)} linked check"
                    f"{'' if len(linked_checks) == 1 else 's'}"
                    f" · {completed_linked} completed"
                )

            with st.expander(
                f"Manage hypothesis · {hypothesis['title']}"
            ):
                current_component = (
                    str(
                        hypothesis.get(
                            "component_id"
                        )
                    )
                    if hypothesis.get(
                        "component_id"
                    )
                    else ""
                )

                if current_component not in component_options:
                    current_component = ""

                with st.form(
                    f"diagnostic_edit_hypothesis_{hypothesis['id']}"
                ):
                    edit_hypothesis_title = st.text_input(
                        "Hypothesis",
                        value=hypothesis[
                            "title"
                        ],
                    )
                    edit_hypothesis_status = st.selectbox(
                        "Evidence state",
                        HYPOTHESIS_STATUSES,
                        index=HYPOTHESIS_STATUSES.index(
                            hypothesis.get(
                                "status",
                                "possible",
                            )
                        ),
                        format_func=_pretty,
                    )
                    edit_hypothesis_component = st.selectbox(
                        "Linked component",
                        component_options,
                        index=component_options.index(
                            current_component
                        ),
                        format_func=lambda item: (
                            component_labels[
                                item
                            ]
                        ),
                    )
                    edit_hypothesis_source = st.selectbox(
                        "Source",
                        HYPOTHESIS_SOURCES,
                        index=HYPOTHESIS_SOURCES.index(
                            hypothesis.get(
                                "source_kind",
                                "user",
                            )
                        ),
                        format_func=_pretty,
                    )
                    edit_hypothesis_rationale = st.text_area(
                        "Rationale",
                        value=(
                            hypothesis.get(
                                "rationale"
                            )
                            or ""
                        ),
                    )

                    save_hypothesis = st.form_submit_button(
                        "Save hypothesis",
                        width="stretch",
                    )

                if save_hypothesis:
                    if not edit_hypothesis_title.strip():
                        st.warning(
                            "Hypothesis cannot be blank."
                        )
                    else:
                        try:
                            update_diagnostic_hypothesis(
                                client,
                                hypothesis[
                                    "id"
                                ],
                                {
                                    "title": edit_hypothesis_title.strip(),
                                    "status": edit_hypothesis_status,
                                    "component_id": (
                                        edit_hypothesis_component
                                        or None
                                    ),
                                    "source_kind": edit_hypothesis_source,
                                    "rationale": (
                                        edit_hypothesis_rationale.strip()
                                        or None
                                    ),
                                },
                            )
                        except Exception as error:
                            st.error(
                                "VCG could not update the hypothesis."
                            )
                            st.exception(
                                error
                            )
                        else:
                            st.rerun()

                confirm_delete_hypothesis = st.checkbox(
                    "Confirm hypothesis deletion",
                    key=(
                        "diagnostic_hypothesis_delete_confirm_"
                        f"{hypothesis['id']}"
                    ),
                )

                if st.button(
                    "Delete hypothesis",
                    key=(
                        "diagnostic_hypothesis_delete_"
                        f"{hypothesis['id']}"
                    ),
                    disabled=(
                        not confirm_delete_hypothesis
                    ),
                    width="stretch",
                ):
                    try:
                        delete_diagnostic_hypothesis(
                            client,
                            hypothesis[
                                "id"
                            ],
                        )
                    except Exception as error:
                        st.error(
                            "VCG could not delete the hypothesis."
                        )
                        st.exception(
                            error
                        )
                    else:
                        st.rerun()

            st.divider()

        with st.expander(
            "＋ Add hypothesis",
            expanded=(
                not case_hypotheses
            ),
        ):
            with st.form(
                f"diagnostic_add_hypothesis_{selected_case_id}",
                clear_on_submit=True,
            ):
                hypothesis_title = st.text_input(
                    "Candidate cause",
                    placeholder="e.g. Binding right-front brake",
                )
                hypothesis_status = st.selectbox(
                    "Evidence state",
                    HYPOTHESIS_STATUSES,
                    index=0,
                    format_func=_pretty,
                )
                hypothesis_component = st.selectbox(
                    "Linked component",
                    component_options,
                    format_func=lambda item: (
                        component_labels[
                            item
                        ]
                    ),
                    key=(
                        "diagnostic_add_hypothesis_component_"
                        f"{selected_case_id}"
                    ),
                )
                hypothesis_source = st.selectbox(
                    "Source",
                    HYPOTHESIS_SOURCES,
                    index=0,
                    format_func=_pretty,
                )
                hypothesis_rationale = st.text_area(
                    "Why is it plausible?",
                    placeholder=(
                        "Record the reasoning/evidence that makes this worth testing."
                    ),
                )

                add_hypothesis = st.form_submit_button(
                    "Add hypothesis",
                    type="primary",
                    width="stretch",
                )

            if add_hypothesis:
                if not hypothesis_title.strip():
                    st.warning(
                        "Enter a candidate cause."
                    )
                else:
                    try:
                        add_diagnostic_hypothesis(
                            client,
                            owner_id,
                            vehicle[
                                "id"
                            ],
                            selected_case_id,
                            {
                                "title": hypothesis_title.strip(),
                                "status": hypothesis_status,
                                "component_id": (
                                    hypothesis_component
                                    or None
                                ),
                                "source_kind": hypothesis_source,
                                "rationale": (
                                    hypothesis_rationale.strip()
                                    or None
                                ),
                            },
                        )
                    except Exception as error:
                        st.error(
                            "VCG could not add the hypothesis."
                        )
                        st.exception(
                            error
                        )
                    else:
                        st.rerun()

    with checks_tab:
        case_hypotheses = snapshot[
            "hypotheses"
        ]

        hypothesis_options = [
            ""
        ] + [
            str(
                hypothesis[
                    "id"
                ]
            )
            for hypothesis in case_hypotheses
        ]

        hypothesis_labels = {
            "": "Case-level / no single hypothesis",
            **{
                str(
                    hypothesis[
                        "id"
                    ]
                ): hypothesis[
                    "title"
                ]
                for hypothesis in case_hypotheses
            },
        }

        st.markdown(
            "#### Planned checks"
        )

        if not snapshot[
            "planned_checks"
        ]:
            st.caption(
                "No diagnostic checks are currently planned."
            )

        for check in snapshot[
            "planned_checks"
        ]:
            linked_hypothesis = (
                hypothesis_labels.get(
                    str(
                        check.get(
                            "hypothesis_id"
                        )
                    ),
                    "No linked hypothesis",
                )
                if check.get(
                    "hypothesis_id"
                )
                else "Case-level"
            )

            component_name = (
                component_names.get(
                    str(
                        check.get(
                            "component_id"
                        )
                    )
                )
                if check.get(
                    "component_id"
                )
                else "Vehicle-level"
            )

            st.markdown(
                f"### {check['title']}"
            )
            st.caption(
                f"{_pretty(check.get('check_type', 'inspection'))}"
                f" · {linked_hypothesis}"
                f" · {component_name}"
            )

            if check.get(
                "procedure"
            ):
                st.write(
                    check[
                        "procedure"
                    ]
                )

            if check.get(
                "safety_notes"
            ):
                st.warning(
                    "Safety: "
                    + str(
                        check[
                            "safety_notes"
                        ]
                    )
                )

            with st.expander(
                f"Record finding · {check['title']}"
            ):
                with st.form(
                    f"diagnostic_complete_check_{check['id']}"
                ):
                    outcome = st.selectbox(
                        "Outcome",
                        CHECK_OUTCOMES,
                        format_func=_pretty,
                    )
                    finding = st.text_area(
                        "Finding",
                        placeholder=(
                            "Record what was actually observed or measured."
                        ),
                    )
                    performed_date = st.date_input(
                        "Performed date",
                        value=date.today(),
                    )
                    performed_mileage = st.text_input(
                        "Vehicle mileage",
                        value=str(
                            int(
                                vehicle.get(
                                    "mileage"
                                )
                                or 0
                            )
                        ),
                    )

                    complete_check = st.form_submit_button(
                        "Complete check",
                        type="primary",
                        width="stretch",
                    )

                if complete_check:
                    if not finding.strip():
                        st.warning(
                            "Record the finding before completing the check."
                        )
                    else:
                        try:
                            update_diagnostic_check(
                                client,
                                check[
                                    "id"
                                ],
                                {
                                    "status": "completed",
                                    "outcome": outcome,
                                    "finding": finding.strip(),
                                    "performed_at": _date_to_timestamptz(
                                        performed_date
                                    ),
                                    "performed_mileage": _optional_mileage(
                                        performed_mileage
                                    ),
                                },
                            )
                        except ValueError as error:
                            st.warning(
                                str(
                                    error
                                )
                            )
                        except Exception as error:
                            st.error(
                                "VCG could not record the diagnostic finding."
                            )
                            st.exception(
                                error
                            )
                        else:
                            st.rerun()

                if st.button(
                    "Skip this check",
                    key=(
                        "diagnostic_skip_check_"
                        f"{check['id']}"
                    ),
                    width="stretch",
                ):
                    try:
                        update_diagnostic_check(
                            client,
                            check[
                                "id"
                            ],
                            {
                                "status": "skipped",
                                "outcome": "not_applicable",
                            },
                        )
                    except Exception as error:
                        st.error(
                            "VCG could not skip the diagnostic check."
                        )
                        st.exception(
                            error
                        )
                    else:
                        st.rerun()

                confirm_delete_check = st.checkbox(
                    "Confirm planned-check deletion",
                    key=(
                        "diagnostic_check_delete_confirm_"
                        f"{check['id']}"
                    ),
                )

                if st.button(
                    "Delete planned check",
                    key=(
                        "diagnostic_check_delete_"
                        f"{check['id']}"
                    ),
                    disabled=(
                        not confirm_delete_check
                    ),
                    width="stretch",
                ):
                    try:
                        delete_diagnostic_check(
                            client,
                            check[
                                "id"
                            ],
                        )
                    except Exception as error:
                        st.error(
                            "VCG could not delete the diagnostic check."
                        )
                        st.exception(
                            error
                        )
                    else:
                        st.rerun()

            st.divider()

        with st.expander(
            "＋ Add diagnostic check",
            expanded=(
                not snapshot[
                    "planned_checks"
                ]
            ),
        ):
            with st.form(
                f"diagnostic_add_check_{selected_case_id}",
                clear_on_submit=True,
            ):
                check_title = st.text_input(
                    "Check",
                    placeholder="e.g. Compare front brake temperatures",
                )
                check_type = st.selectbox(
                    "Check type",
                    CHECK_TYPES,
                    index=1,
                    format_func=_pretty,
                )
                linked_hypothesis = st.selectbox(
                    "Tests hypothesis",
                    hypothesis_options,
                    format_func=lambda item: (
                        hypothesis_labels[
                            item
                        ]
                    ),
                )
                check_component = st.selectbox(
                    "Linked component",
                    component_options,
                    format_func=lambda item: (
                        component_labels[
                            item
                        ]
                    ),
                    key=(
                        "diagnostic_add_check_component_"
                        f"{selected_case_id}"
                    ),
                )
                procedure = st.text_area(
                    "Procedure",
                    placeholder=(
                        "What should be checked or measured? Keep it specific."
                    ),
                )
                safety_notes = st.text_area(
                    "Safety notes",
                    placeholder=(
                        "Optional. Record any precautions before carrying this out."
                    ),
                )

                add_check = st.form_submit_button(
                    "Add planned check",
                    type="primary",
                    width="stretch",
                )

            if add_check:
                if not check_title.strip():
                    st.warning(
                        "Enter a diagnostic check."
                    )
                else:
                    try:
                        add_diagnostic_check(
                            client,
                            owner_id,
                            vehicle[
                                "id"
                            ],
                            selected_case_id,
                            {
                                "title": check_title.strip(),
                                "check_type": check_type,
                                "hypothesis_id": (
                                    linked_hypothesis
                                    or None
                                ),
                                "component_id": (
                                    check_component
                                    or None
                                ),
                                "procedure": (
                                    procedure.strip()
                                    or None
                                ),
                                "safety_notes": (
                                    safety_notes.strip()
                                    or None
                                ),
                                "status": "planned",
                            },
                        )
                    except Exception as error:
                        st.error(
                            "VCG could not add the diagnostic check."
                        )
                        st.exception(
                            error
                        )
                    else:
                        st.rerun()

        st.markdown(
            "#### Completed evidence"
        )

        if not snapshot[
            "completed_checks"
        ]:
            st.caption(
                "No diagnostic checks have been completed yet."
            )

        for check in snapshot[
            "completed_checks"
        ]:
            st.markdown(
                f"**{check['title']}**"
            )

            st.caption(
                f"Outcome: {_pretty(check.get('outcome', 'inconclusive'))}"
                + (
                    f" · {str(check['performed_at'])[:10]}"
                    if check.get(
                        "performed_at"
                    )
                    else ""
                )
                + (
                    f" · {int(check['performed_mileage']):,} mi"
                    if check.get(
                        "performed_mileage"
                    )
                    is not None
                    else ""
                )
            )

            st.write(
                check.get(
                    "finding"
                )
                or "No finding recorded."
            )

            st.divider()

    with resolution_tab:
        if selected_case.get(
            "status"
        ) in {
            "resolved",
            "closed",
        }:
            st.success(
                f"Case {_pretty(selected_case['status'])}."
            )

            if selected_case.get(
                "resolution_summary"
            ):
                st.markdown(
                    "#### Recorded resolution"
                )
                st.write(
                    selected_case[
                        "resolution_summary"
                    ]
                )

            if st.button(
                "Reopen investigation",
                key=(
                    "diagnostic_reopen_"
                    f"{selected_case_id}"
                ),
                width="stretch",
            ):
                try:
                    update_diagnostic_case(
                        client,
                        selected_case_id,
                        {
                            "status": "open",
                            "resolved_at": None,
                            "resolution_summary": None,
                        },
                    )
                except Exception as error:
                    st.error(
                        "VCG could not reopen the diagnostic case."
                    )
                    st.exception(
                        error
                    )
                else:
                    st.rerun()
        else:
            st.caption(
                "Resolve only when the investigation record supports an outcome. "
                "Closing without a confirmed cause is also valid."
            )

            with st.form(
                f"diagnostic_resolve_{selected_case_id}"
            ):
                close_mode = st.selectbox(
                    "Case outcome",
                    [
                        "resolved",
                        "closed",
                    ],
                    format_func=lambda value: (
                        "Resolved"
                        if value == "resolved"
                        else "Closed without confirmed cause"
                    ),
                )
                resolution_summary = st.text_area(
                    "Resolution / closing summary",
                    placeholder=(
                        "What was established, repaired, ruled out, or left unconfirmed?"
                    ),
                )
                final_drive_risk = st.selectbox(
                    "Drive-risk record after closure",
                    DRIVE_RISKS,
                    index=DRIVE_RISKS.index(
                        selected_case.get(
                            "drive_risk",
                            "unknown",
                        )
                    ),
                    format_func=_pretty,
                )

                resolve_case = st.form_submit_button(
                    "Close investigation",
                    type="primary",
                    width="stretch",
                )

            if resolve_case:
                if not resolution_summary.strip():
                    st.warning(
                        "Record a closing summary."
                    )
                else:
                    try:
                        update_diagnostic_case(
                            client,
                            selected_case_id,
                            {
                                "status": close_mode,
                                "resolution_summary": resolution_summary.strip(),
                                "drive_risk": final_drive_risk,
                                "resolved_at": datetime.now(
                                    timezone.utc
                                ).isoformat(),
                            },
                        )
                    except Exception as error:
                        st.error(
                            "VCG could not close the diagnostic case."
                        )
                        st.exception(
                            error
                        )
                    else:
                        st.rerun()

        st.divider()
        st.markdown(
            "#### Danger zone"
        )

        confirm_case_delete = st.checkbox(
            "Delete this case and all its hypotheses/checks",
            key=(
                "diagnostic_case_delete_confirm_"
                f"{selected_case_id}"
            ),
        )

        if st.button(
            "Delete diagnostic case",
            key=(
                "diagnostic_case_delete_"
                f"{selected_case_id}"
            ),
            disabled=(
                not confirm_case_delete
            ),
            width="stretch",
        ):
            try:
                delete_diagnostic_case(
                    client,
                    selected_case_id,
                )
            except Exception as error:
                st.error(
                    "VCG could not delete the diagnostic case."
                )
                st.exception(
                    error
                )
            else:
                st.session_state.pop(
                    focus_key,
                    None,
                )
                st.rerun()
