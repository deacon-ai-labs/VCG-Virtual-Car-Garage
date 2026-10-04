from __future__ import annotations

from datetime import date

import streamlit as st
from ui_errors import log_ui_exception

from database import (
    add_maintenance_item,
    complete_maintenance_item,
    delete_maintenance_item,
    record_maintenance_history,
    update_maintenance_item,
)
from maintenance_os import (
    maintenance_due_label,
    maintenance_health_snapshot,
    maintenance_is_due_soon,
    maintenance_is_overdue,
    maintenance_recurrence_label,
)


CATEGORIES = [
    "service",
    "fluid",
    "consumable",
    "inspection",
    "repair",
    "advisory",
]

PRIORITIES = [
    "low",
    "normal",
    "high",
    "critical",
]


def _coerce_date(
    value,
) -> date | None:
    """Normalise Supabase date values for Streamlit date widgets."""

    if value is None:
        return None

    if isinstance(
        value,
        date,
    ):
        return value

    try:
        return date.fromisoformat(
            str(value)[:10]
        )
    except ValueError:
        return None


def _optional_int(
    value: str,
    field_name: str,
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
            f"{field_name} must be a whole number."
        ) from error

    if parsed < 0:
        raise ValueError(
            f"{field_name} cannot be negative."
        )

    return parsed


def _optional_positive_int(
    value: str,
    field_name: str,
) -> int | None:
    parsed = _optional_int(
        value,
        field_name,
    )

    if parsed is not None and parsed <= 0:
        raise ValueError(
            f"{field_name} must be greater than zero."
        )

    return parsed


def _optional_money(
    value: str,
    field_name: str,
) -> float | None:
    clean = value.strip()

    if not clean:
        return None

    try:
        parsed = float(
            clean
        )
    except ValueError as error:
        raise ValueError(
            f"{field_name} must be a number."
        ) from error

    if parsed < 0:
        raise ValueError(
            f"{field_name} cannot be negative."
        )

    return round(
        parsed,
        2,
    )


def _component_options(
    components: list[dict],
) -> tuple[list[str], dict[str, str]]:
    ordered = sorted(
        [
            component
            for component in components
            if component.get(
                "lifecycle_status"
            ) != "cancelled"
        ],
        key=lambda component: (
            component.get(
                "sort_order",
                0,
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
        "": "Vehicle / not linked",
    }

    system_labels = {
        component.get(
            "system_key"
        ): component.get(
            "name"
        )
        for component in ordered
        if component.get(
            "component_type"
        ) == "system"
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
                system_labels.get(
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


def render_maintenance_os(
    client,
    owner_id: str,
    vehicle: dict,
    items: list[dict],
    records: list[dict],
    components: list[dict],
) -> None:
    """Render the full M15 maintenance and vehicle-health workspace."""

    current_mileage = int(
        vehicle.get(
            "mileage"
        )
        or 0
    )

    snapshot = (
        maintenance_health_snapshot(
            items,
            records,
            current_mileage,
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
                <div class="vcg-section-kicker">MAINTENANCE & VEHICLE HEALTH</div>
                <div class="vcg-section-title">Maintenance OS</div>
            </div>
            <div class="vcg-live-pill">EVIDENCE BASED</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(
        "Health is based on recorded due points and service history. "
        "VCG does not invent a synthetic health percentage."
    )

    (
        metric_state,
        metric_overdue,
        metric_soon,
        metric_history,
        metric_spend,
    ) = st.columns(
        5
    )

    with metric_state:
        st.metric(
            "Status",
            snapshot[
                "state"
            ],
            border=True,
        )

    with metric_overdue:
        st.metric(
            "Overdue",
            snapshot[
                "overdue_count"
            ],
            border=True,
        )

    with metric_soon:
        st.metric(
            "Due soon",
            snapshot[
                "due_soon_count"
            ],
            border=True,
        )

    with metric_history:
        st.metric(
            "History",
            snapshot[
                "history_count"
            ],
            border=True,
        )

    with metric_spend:
        st.metric(
            "Recorded spend",
            (
                f"£{snapshot['lifetime_cost_gbp']:,.2f}"
                if snapshot[
                    "lifetime_cost_gbp"
                ]
                else "£0"
            ),
            border=True,
        )

    if snapshot[
        "overdue_count"
    ]:
        st.error(
            f"{snapshot['overdue_count']} maintenance item"
            f"{'' if snapshot['overdue_count'] == 1 else 's'} "
            "have reached a recorded due point."
        )
    elif snapshot[
        "due_soon_count"
    ]:
        st.warning(
            f"{snapshot['due_soon_count']} maintenance item"
            f"{'' if snapshot['due_soon_count'] == 1 else 's'} "
            "are approaching a recorded due point."
        )
    elif snapshot[
        "pending_count"
    ]:
        st.info(
            "Maintenance is planned with nothing currently overdue "
            "or inside the due-soon window."
        )
    else:
        st.success(
            "No open maintenance items are currently recorded."
        )

    next_actions = snapshot[
        "next_actions"
    ][:3]

    if next_actions:
        st.markdown(
            "#### What needs attention next"
        )

        action_columns = st.columns(
            len(
                next_actions
            )
        )

        for column, item in zip(
            action_columns,
            next_actions,
        ):
            with column:
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
                    attention = (
                        item.get(
                            "priority",
                            "normal",
                        ).upper()
                    )

                st.markdown(
                    f"**{item['title']}**"
                )
                st.caption(
                    f"{attention} · "
                    f"{maintenance_due_label(item)}"
                )

    schedule_tab, history_tab, add_tab = (
        st.tabs(
            [
                "Schedule",
                "Service history",
                "Add / record",
            ]
        )
    )

    with schedule_tab:
        open_items = snapshot[
            "next_actions"
        ]

        if not open_items:
            st.caption(
                "No open maintenance schedules."
            )

        for item in open_items:
            linked_name = (
                component_names.get(
                    str(
                        item.get(
                            "twin_component_id"
                        )
                    )
                )
                if item.get(
                    "twin_component_id"
                )
                else None
            )

            st.markdown(
                f"### {item['title']}"
            )

            meta = [
                str(
                    item.get(
                        "category",
                        "service",
                    )
                ).title(),
                str(
                    item.get(
                        "priority",
                        "normal",
                    )
                ).title(),
                maintenance_due_label(
                    item
                ),
                maintenance_recurrence_label(
                    item
                ),
            ]

            if linked_name:
                meta.append(
                    linked_name
                )

            if item.get(
                "estimated_cost_gbp"
            ) is not None:
                meta.append(
                    f"Est. £{float(item['estimated_cost_gbp']):,.2f}"
                )

            st.caption(
                " · ".join(
                    meta
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

            with st.expander(
                f"Complete / service · {item['title']}"
            ):
                with st.form(
                    f"complete_maintenance_{item['id']}"
                ):
                    performed_at = st.date_input(
                        "Performed date",
                        value=date.today(),
                        key=(
                            "maintenance_done_date_"
                            f"{item['id']}"
                        ),
                    )
                    performed_mileage = st.text_input(
                        "Mileage",
                        value=str(
                            current_mileage
                        ),
                        key=(
                            "maintenance_done_mileage_"
                            f"{item['id']}"
                        ),
                    )
                    cost = st.text_input(
                        "Actual cost (£)",
                        placeholder="Optional",
                        key=(
                            "maintenance_done_cost_"
                            f"{item['id']}"
                        ),
                    )
                    provider = st.text_input(
                        "Garage / provider",
                        placeholder="Optional",
                        key=(
                            "maintenance_done_provider_"
                            f"{item['id']}"
                        ),
                    )
                    completion_notes = st.text_area(
                        "Work notes",
                        placeholder="What was done, findings, parts used...",
                        key=(
                            "maintenance_done_notes_"
                            f"{item['id']}"
                        ),
                    )
                    evidence_reference = st.text_input(
                        "Evidence / receipt reference",
                        placeholder="Optional filename, invoice number or URL",
                        key=(
                            "maintenance_done_evidence_"
                            f"{item['id']}"
                        ),
                    )

                    complete_submitted = (
                        st.form_submit_button(
                            "Record completed work",
                            type="primary",
                            width="stretch",
                        )
                    )

                if complete_submitted:
                    try:
                        parsed_mileage = (
                            _optional_int(
                                performed_mileage,
                                "Mileage",
                            )
                        )
                        parsed_cost = (
                            _optional_money(
                                cost,
                                "Actual cost",
                            )
                        )

                        complete_maintenance_item(
                            client,
                            item[
                                "id"
                            ],
                            performed_at,
                            performed_mileage=(
                                parsed_mileage
                            ),
                            cost_gbp=(
                                parsed_cost
                            ),
                            provider=provider,
                            notes=completion_notes,
                            evidence_reference=(
                                evidence_reference
                            ),
                        )
                    except ValueError as error:
                        st.warning(
                            str(
                                error
                            )
                        )
                    except Exception as error:
                        st.error(
                            "VCG could not record the completed maintenance."
                        )
                        log_ui_exception(error)
                    else:
                        st.rerun()

            with st.expander(
                f"Edit schedule · {item['title']}"
            ):
                current_component = (
                    str(
                        item.get(
                            "twin_component_id"
                        )
                    )
                    if item.get(
                        "twin_component_id"
                    )
                    else ""
                )

                if current_component not in component_options:
                    current_component = ""

                with st.form(
                    f"edit_maintenance_{item['id']}"
                ):
                    edit_category = st.selectbox(
                        "Category",
                        CATEGORIES,
                        index=(
                            CATEGORIES.index(
                                item.get(
                                    "category",
                                    "service",
                                )
                            )
                            if item.get(
                                "category",
                                "service",
                            )
                            in CATEGORIES
                            else 0
                        ),
                        key=(
                            "maintenance_edit_category_"
                            f"{item['id']}"
                        ),
                    )
                    edit_priority = st.selectbox(
                        "Priority",
                        PRIORITIES,
                        index=(
                            PRIORITIES.index(
                                item.get(
                                    "priority",
                                    "normal",
                                )
                            )
                            if item.get(
                                "priority",
                                "normal",
                            )
                            in PRIORITIES
                            else 1
                        ),
                        key=(
                            "maintenance_edit_priority_"
                            f"{item['id']}"
                        ),
                    )
                    edit_component = st.selectbox(
                        "Digital-twin link",
                        component_options,
                        index=component_options.index(
                            current_component
                        ),
                        format_func=lambda component_id: (
                            component_labels[
                                component_id
                            ]
                        ),
                        key=(
                            "maintenance_edit_component_"
                            f"{item['id']}"
                        ),
                    )
                    edit_due_mileage = st.text_input(
                        "Due mileage",
                        value=(
                            str(
                                item[
                                    "due_mileage"
                                ]
                            )
                            if item.get(
                                "due_mileage"
                            )
                            is not None
                            else ""
                        ),
                        key=(
                            "maintenance_edit_due_mileage_"
                            f"{item['id']}"
                        ),
                    )
                    edit_due_date = st.date_input(
                        "Due date",
                        value=_coerce_date(
                            item.get(
                                "due_date"
                            )
                        ),
                        key=(
                            "maintenance_edit_due_date_"
                            f"{item['id']}"
                        ),
                    )
                    edit_interval_miles = st.text_input(
                        "Repeat every miles",
                        value=(
                            str(
                                item[
                                    "interval_miles"
                                ]
                            )
                            if item.get(
                                "interval_miles"
                            )
                            is not None
                            else ""
                        ),
                        key=(
                            "maintenance_edit_interval_miles_"
                            f"{item['id']}"
                        ),
                    )
                    edit_interval_months = st.text_input(
                        "Repeat every months",
                        value=(
                            str(
                                item[
                                    "interval_months"
                                ]
                            )
                            if item.get(
                                "interval_months"
                            )
                            is not None
                            else ""
                        ),
                        key=(
                            "maintenance_edit_interval_months_"
                            f"{item['id']}"
                        ),
                    )
                    edit_estimated_cost = st.text_input(
                        "Estimated cost (£)",
                        value=(
                            str(
                                item[
                                    "estimated_cost_gbp"
                                ]
                            )
                            if item.get(
                                "estimated_cost_gbp"
                            )
                            is not None
                            else ""
                        ),
                        key=(
                            "maintenance_edit_estimated_cost_"
                            f"{item['id']}"
                        ),
                    )
                    edit_notes = st.text_area(
                        "Notes",
                        value=(
                            item.get(
                                "notes"
                            )
                            or ""
                        ),
                        key=(
                            "maintenance_edit_notes_"
                            f"{item['id']}"
                        ),
                    )

                    update_submitted = (
                        st.form_submit_button(
                            "Update schedule",
                            width="stretch",
                        )
                    )

                if update_submitted:
                    try:
                        changes = {
                            "category": edit_category,
                            "priority": edit_priority,
                            "twin_component_id": (
                                edit_component
                                or None
                            ),
                            "due_mileage": _optional_int(
                                edit_due_mileage,
                                "Due mileage",
                            ),
                            "due_date": (
                                edit_due_date.isoformat()
                                if edit_due_date
                                else None
                            ),
                            "interval_miles": _optional_positive_int(
                                edit_interval_miles,
                                "Mileage interval",
                            ),
                            "interval_months": _optional_positive_int(
                                edit_interval_months,
                                "Month interval",
                            ),
                            "estimated_cost_gbp": _optional_money(
                                edit_estimated_cost,
                                "Estimated cost",
                            ),
                            "notes": (
                                edit_notes.strip()
                                or None
                            ),
                        }

                        update_maintenance_item(
                            client,
                            item[
                                "id"
                            ],
                            changes,
                        )
                    except ValueError as error:
                        st.warning(
                            str(
                                error
                            )
                        )
                    except Exception as error:
                        st.error(
                            "VCG could not update the maintenance schedule."
                        )
                        log_ui_exception(error)
                    else:
                        st.rerun()

                confirm_delete = st.checkbox(
                    "Confirm schedule deletion",
                    key=(
                        "maintenance_delete_confirm_"
                        f"{item['id']}"
                    ),
                )

                if st.button(
                    "Delete schedule",
                    key=(
                        "maintenance_delete_"
                        f"{item['id']}"
                    ),
                    disabled=(
                        not confirm_delete
                    ),
                    width="stretch",
                ):
                    try:
                        delete_maintenance_item(
                            client,
                            item[
                                "id"
                            ],
                        )
                    except Exception as error:
                        st.error(
                            "VCG could not delete the maintenance schedule."
                        )
                        log_ui_exception(error)
                    else:
                        st.rerun()

            st.divider()

    with history_tab:
        st.caption(
            "Service history is append-only. New corrections should be "
            "recorded as additional evidence rather than silently rewriting history."
        )

        if not records:
            st.caption(
                "No service-history records have been added yet."
            )

        for record in records:
            st.markdown(
                f"### {record['title']}"
            )

            history_meta = [
                str(
                    record.get(
                        "category",
                        "service",
                    )
                ).title(),
                str(
                    record.get(
                        "performed_at",
                        "Unknown date",
                    )
                ),
            ]

            if record.get(
                "performed_mileage"
            ) is not None:
                history_meta.append(
                    f"{int(record['performed_mileage']):,} mi"
                )

            if record.get(
                "cost_gbp"
            ) is not None:
                history_meta.append(
                    f"£{float(record['cost_gbp']):,.2f}"
                )

            if record.get(
                "provider"
            ):
                history_meta.append(
                    record[
                        "provider"
                    ]
                )

            linked_component = (
                component_names.get(
                    str(
                        record.get(
                            "twin_component_id"
                        )
                    )
                )
                if record.get(
                    "twin_component_id"
                )
                else None
            )

            if linked_component:
                history_meta.append(
                    linked_component
                )

            st.caption(
                " · ".join(
                    history_meta
                )
            )

            if record.get(
                "notes"
            ):
                st.write(
                    record[
                        "notes"
                    ]
                )

            if record.get(
                "evidence_reference"
            ):
                st.caption(
                    "Evidence: "
                    + str(
                        record[
                            "evidence_reference"
                        ]
                    )
                )

            st.divider()

    with add_tab:
        schedule_add_tab, history_add_tab = (
            st.tabs(
                [
                    "Schedule future work",
                    "Record past work",
                ]
            )
        )

        with schedule_add_tab:
            with st.form(
                "add_maintenance_schedule",
                clear_on_submit=True,
            ):
                title = st.text_input(
                    "Maintenance item",
                    placeholder="e.g. Engine oil and filter",
                )
                category = st.selectbox(
                    "Category",
                    CATEGORIES,
                )
                priority = st.selectbox(
                    "Priority",
                    PRIORITIES,
                    index=1,
                )
                component_id = st.selectbox(
                    "Digital-twin link",
                    component_options,
                    format_func=lambda selected: (
                        component_labels[
                            selected
                        ]
                    ),
                )
                due_mileage = st.text_input(
                    "Due mileage",
                    placeholder="Optional",
                )
                due_date = st.date_input(
                    "Due date",
                    value=None,
                )
                interval_miles = st.text_input(
                    "Repeat every miles",
                    placeholder="Optional",
                )
                interval_months = st.text_input(
                    "Repeat every months",
                    placeholder="Optional",
                )
                estimated_cost = st.text_input(
                    "Estimated cost (£)",
                    placeholder="Optional",
                )
                notes = st.text_area(
                    "Notes",
                    placeholder="Scope, parts, checks or other context",
                )

                add_schedule = st.form_submit_button(
                    "Add maintenance schedule",
                    type="primary",
                    width="stretch",
                )

            if add_schedule:
                if not title.strip():
                    st.warning(
                        "Enter a maintenance item."
                    )
                else:
                    try:
                        item_data = {
                            "title": title.strip(),
                            "category": category,
                            "priority": priority,
                            "status": "pending",
                            "twin_component_id": (
                                component_id
                                or None
                            ),
                            "due_mileage": _optional_int(
                                due_mileage,
                                "Due mileage",
                            ),
                            "due_date": (
                                due_date.isoformat()
                                if due_date
                                else None
                            ),
                            "interval_miles": _optional_positive_int(
                                interval_miles,
                                "Mileage interval",
                            ),
                            "interval_months": _optional_positive_int(
                                interval_months,
                                "Month interval",
                            ),
                            "estimated_cost_gbp": _optional_money(
                                estimated_cost,
                                "Estimated cost",
                            ),
                            "notes": (
                                notes.strip()
                                or None
                            ),
                        }

                        add_maintenance_item(
                            client,
                            owner_id,
                            vehicle[
                                "id"
                            ],
                            item_data,
                        )
                    except ValueError as error:
                        st.warning(
                            str(
                                error
                            )
                        )
                    except Exception as error:
                        st.error(
                            "VCG could not create the maintenance schedule."
                        )
                        log_ui_exception(error)
                    else:
                        st.rerun()

        with history_add_tab:
            with st.form(
                "record_past_maintenance",
                clear_on_submit=True,
            ):
                historic_title = st.text_input(
                    "Work performed",
                    placeholder="e.g. Front brake fluid change",
                )
                historic_category = st.selectbox(
                    "Category",
                    CATEGORIES,
                    key="historic_maintenance_category",
                )
                historic_component = st.selectbox(
                    "Digital-twin link",
                    component_options,
                    format_func=lambda selected: (
                        component_labels[
                            selected
                        ]
                    ),
                    key="historic_maintenance_component",
                )
                historic_date = st.date_input(
                    "Performed date",
                    value=date.today(),
                    key="historic_maintenance_date",
                )
                historic_mileage = st.text_input(
                    "Mileage",
                    placeholder="Optional",
                    key="historic_maintenance_mileage",
                )
                historic_cost = st.text_input(
                    "Cost (£)",
                    placeholder="Optional",
                    key="historic_maintenance_cost",
                )
                historic_provider = st.text_input(
                    "Garage / provider",
                    placeholder="Optional",
                )
                historic_notes = st.text_area(
                    "Notes",
                    placeholder="Work completed, findings, parts used...",
                    key="historic_maintenance_notes",
                )
                historic_evidence = st.text_input(
                    "Evidence / receipt reference",
                    placeholder="Optional filename, invoice number or URL",
                    key="historic_maintenance_evidence",
                )

                record_history = st.form_submit_button(
                    "Add service-history record",
                    type="primary",
                    width="stretch",
                )

            if record_history:
                if not historic_title.strip():
                    st.warning(
                        "Enter the work that was performed."
                    )
                else:
                    try:
                        record_maintenance_history(
                            client,
                            vehicle[
                                "id"
                            ],
                            historic_title.strip(),
                            historic_category,
                            historic_date,
                            performed_mileage=(
                                _optional_int(
                                    historic_mileage,
                                    "Mileage",
                                )
                            ),
                            cost_gbp=(
                                _optional_money(
                                    historic_cost,
                                    "Cost",
                                )
                            ),
                            provider=(
                                historic_provider
                            ),
                            notes=(
                                historic_notes
                            ),
                            evidence_reference=(
                                historic_evidence
                            ),
                            twin_component_id=(
                                historic_component
                                or None
                            ),
                        )
                    except ValueError as error:
                        st.warning(
                            str(
                                error
                            )
                        )
                    except Exception as error:
                        st.error(
                            "VCG could not record the historic maintenance."
                        )
                        log_ui_exception(error)
                    else:
                        st.rerun()
