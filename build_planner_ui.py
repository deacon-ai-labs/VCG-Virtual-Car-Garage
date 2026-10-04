from __future__ import annotations

from datetime import date

import streamlit as st
from ui_errors import log_ui_exception

from build_planner import build_plan_snapshot
from database import (
    cancel_build_plan_item,
    complete_build_plan_item,
    create_build_plan_install,
    create_build_plan_removal,
    update_build_plan_item,
)


PLAN_STATUSES = [
    "wishlist",
    "planned",
    "ready",
]

PRIORITIES = [
    "low",
    "normal",
    "high",
]

COMPATIBILITY_STATUSES = [
    "unknown",
    "needs_review",
    "compatible",
    "incompatible",
]


def _optional_money(
    value: str,
    field_name: str,
) -> float | None:
    clean = value.strip()

    if not clean:
        return None

    try:
        parsed = float(clean)
    except ValueError as error:
        raise ValueError(
            f"{field_name} must be a number."
        ) from error

    if parsed < 0:
        raise ValueError(
            f"{field_name} cannot be negative."
        )

    return round(parsed, 2)


def _optional_weight(
    value: str,
) -> float | None:
    clean = value.strip()

    if not clean:
        return None

    try:
        parsed = float(clean)
    except ValueError as error:
        raise ValueError(
            "Weight must be a number in kilograms."
        ) from error

    if parsed < 0:
        raise ValueError(
            "Weight cannot be negative."
        )

    return parsed


def _optional_mileage(
    value: str,
) -> int | None:
    clean = value.strip()

    if not clean:
        return None

    try:
        parsed = int(clean)
    except ValueError as error:
        raise ValueError(
            "Mileage must be a whole number."
        ) from error

    if parsed < 0:
        raise ValueError(
            "Mileage cannot be negative."
        )

    return parsed


def _coerce_date(
    value,
) -> date | None:
    if value is None:
        return None

    if isinstance(value, date):
        return value

    try:
        return date.fromisoformat(
            str(value)[:10]
        )
    except ValueError:
        return None


def _component_name(
    item: dict,
    component_lookup: dict[str, dict],
) -> str:
    component = component_lookup.get(
        str(item.get("component_id")),
        {},
    )

    return component.get(
        "name",
        "Unknown component",
    )


def render_build_planner(
    client,
    vehicle: dict,
    components: list[dict],
    plan_items: list[dict],
) -> None:
    """Render the M16 build planning workspace."""

    snapshot = build_plan_snapshot(
        plan_items,
        components,
    )

    component_lookup = snapshot[
        "component_lookup"
    ]

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

    system_names = {
        system["system_key"]: system["name"]
        for system in root_systems
    }

    st.markdown(
        """
        <div class="vcg-section-heading">
            <div>
                <div class="vcg-section-kicker">MODIFICATION INTELLIGENCE</div>
                <div class="vcg-section-title">Build Planner</div>
            </div>
            <div class="vcg-live-pill">CURRENT ≠ PLANNED</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(
        "Future changes stay separate from the physical digital twin "
        "until you explicitly mark them installed or removed."
    )

    (
        installed_col,
        changes_col,
        budget_col,
        weight_col,
        review_col,
    ) = st.columns(5)

    with installed_col:
        st.metric(
            "Installed",
            snapshot[
                "current_installed_count"
            ],
            border=True,
        )

    with changes_col:
        st.metric(
            "Active changes",
            snapshot[
                "active_count"
            ],
            border=True,
        )

    with budget_col:
        st.metric(
            "Est. plan cost",
            (
                f"£{snapshot['estimated_cost_gbp']:,.2f}"
                if snapshot["estimated_cost_gbp"]
                else "£0"
            ),
            border=True,
        )

    with weight_col:
        st.metric(
            "Known weight Δ",
            f"{snapshot['known_weight_delta_kg']:+.1f} kg",
            border=True,
        )

    with review_col:
        st.metric(
            "Needs review",
            snapshot[
                "compatibility_review_count"
            ],
            border=True,
        )

    if snapshot["incompatible_count"]:
        st.error(
            f"{snapshot['incompatible_count']} planned install"
            f"{'' if snapshot['incompatible_count'] == 1 else 's'} "
            "are marked incompatible."
        )
    elif snapshot["compatibility_review_count"]:
        st.warning(
            f"{snapshot['compatibility_review_count']} planned install"
            f"{'' if snapshot['compatibility_review_count'] == 1 else 's'} "
            "still need compatibility review."
        )

    (
        compare_tab,
        plan_tab,
        add_tab,
        history_tab,
    ) = st.tabs(
        [
            "Compare",
            "Active plan",
            "Add change",
            "History",
        ]
    )

    with compare_tab:
        current_col, future_col = st.columns(
            2,
            gap="large",
        )

        with current_col:
            st.markdown(
                "### Current physical build"
            )

            if not snapshot["current_installed"]:
                st.caption(
                    "No installed structured components recorded."
                )

            for component in snapshot[
                "current_installed"
            ]:
                st.markdown(
                    f"**{component['name']}**"
                )

                meta = [
                    str(
                        system_names.get(
                            component.get("system_key"),
                            component.get(
                                "system_key",
                                "Other",
                            ),
                        )
                    )
                ]

                if component.get("manufacturer"):
                    meta.append(
                        str(
                            component[
                                "manufacturer"
                            ]
                        )
                    )

                if component.get("weight_kg") is not None:
                    meta.append(
                        f"{float(component['weight_kg']):.1f} kg"
                    )

                st.caption(
                    " · ".join(meta)
                )

        with future_col:
            st.markdown(
                "### Planned changes"
            )

            if not snapshot["active_items"]:
                st.caption(
                    "No active build-plan changes."
                )

            for item in snapshot[
                "active_items"
            ]:
                component = component_lookup.get(
                    str(item.get("component_id")),
                    {},
                )

                prefix = (
                    "+"
                    if item.get("action") == "install"
                    else "−"
                )

                st.markdown(
                    f"**{prefix} "
                    f"{component.get('name', 'Unknown component')}**"
                )

                meta = [
                    str(
                        item.get(
                            "status",
                            "planned",
                        )
                    ).title(),
                    str(
                        system_names.get(
                            component.get("system_key"),
                            component.get(
                                "system_key",
                                "Other",
                            ),
                        )
                    ),
                ]

                if item.get("estimated_cost_gbp") is not None:
                    meta.append(
                        f"£{float(item['estimated_cost_gbp']):,.2f}"
                    )

                if component.get("weight_kg") is not None:
                    weight_prefix = (
                        "+"
                        if item.get("action") == "install"
                        else "−"
                    )
                    meta.append(
                        f"{weight_prefix}"
                        f"{float(component['weight_kg']):.1f} kg"
                    )

                st.caption(
                    " · ".join(meta)
                )

        st.divider()

        (
            current_weight_col,
            delta_col,
            projected_col,
            systems_col,
        ) = st.columns(4)

        with current_weight_col:
            st.metric(
                "Known current weight",
                f"{snapshot['current_known_weight_kg']:.1f} kg",
                border=True,
            )

        with delta_col:
            st.metric(
                "Known plan delta",
                f"{snapshot['known_weight_delta_kg']:+.1f} kg",
                border=True,
            )

        with projected_col:
            st.metric(
                "Projected known weight",
                f"{snapshot['projected_known_weight_kg']:.1f} kg",
                border=True,
            )

        with systems_col:
            st.metric(
                "Systems affected",
                len(
                    snapshot[
                        "affected_systems"
                    ]
                ),
                border=True,
            )

        if snapshot["unknown_weight_actions"]:
            st.info(
                f"{snapshot['unknown_weight_actions']} active change"
                f"{'' if snapshot['unknown_weight_actions'] == 1 else 's'} "
                "have no recorded component weight. VCG leaves the "
                "weight comparison incomplete rather than guessing."
            )

    with plan_tab:
        if not snapshot["active_items"]:
            st.caption(
                "Nothing is currently in the active build plan."
            )

        for item in snapshot["active_items"]:
            component_name = _component_name(
                item,
                component_lookup,
            )
            action = item.get(
                "action",
                "install",
            )

            st.markdown(
                f"### "
                f"{'Install' if action == 'install' else 'Remove'}: "
                f"{component_name}"
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

            if item.get("target_date"):
                meta.append(
                    "Target "
                    + str(
                        item[
                            "target_date"
                        ]
                    )
                )

            if item.get("estimated_cost_gbp") is not None:
                meta.append(
                    f"Est. £{float(item['estimated_cost_gbp']):,.2f}"
                )

            if action == "install":
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
                " · ".join(meta)
            )

            if item.get("compatibility_notes"):
                st.caption(
                    "Compatibility: "
                    + str(
                        item[
                            "compatibility_notes"
                        ]
                    )
                )

            if item.get("notes"):
                st.write(
                    item[
                        "notes"
                    ]
                )

            with st.expander(
                f"Manage · {component_name}"
            ):
                with st.form(
                    f"edit_plan_{item['id']}"
                ):
                    edit_status = st.selectbox(
                        "Plan state",
                        PLAN_STATUSES,
                        index=PLAN_STATUSES.index(
                            item.get(
                                "status",
                                "planned",
                            )
                        ),
                        key=(
                            "plan_status_"
                            f"{item['id']}"
                        ),
                    )
                    edit_priority = st.selectbox(
                        "Priority",
                        PRIORITIES,
                        index=PRIORITIES.index(
                            item.get(
                                "priority",
                                "normal",
                            )
                        ),
                        key=(
                            "plan_priority_"
                            f"{item['id']}"
                        ),
                    )
                    edit_cost = st.text_input(
                        "Estimated cost (£)",
                        value=(
                            str(
                                item[
                                    "estimated_cost_gbp"
                                ]
                            )
                            if item.get("estimated_cost_gbp") is not None
                            else ""
                        ),
                        key=(
                            "plan_cost_"
                            f"{item['id']}"
                        ),
                    )
                    edit_target = st.date_input(
                        "Target date",
                        value=_coerce_date(
                            item.get(
                                "target_date"
                            )
                        ),
                        key=(
                            "plan_target_"
                            f"{item['id']}"
                        ),
                    )

                    if action == "install":
                        compatibility_status = st.selectbox(
                            "Compatibility status",
                            COMPATIBILITY_STATUSES,
                            index=COMPATIBILITY_STATUSES.index(
                                item.get(
                                    "compatibility_status",
                                    "unknown",
                                )
                            ),
                            key=(
                                "plan_compat_"
                                f"{item['id']}"
                            ),
                        )
                        compatibility_notes = st.text_area(
                            "Compatibility notes",
                            value=(
                                item.get(
                                    "compatibility_notes"
                                )
                                or ""
                            ),
                            key=(
                                "plan_compat_notes_"
                                f"{item['id']}"
                            ),
                        )
                    else:
                        compatibility_status = (
                            item.get(
                                "compatibility_status"
                            )
                            or "unknown"
                        )
                        compatibility_notes = (
                            item.get(
                                "compatibility_notes"
                            )
                            or ""
                        )

                    edit_notes = st.text_area(
                        "Plan notes",
                        value=(
                            item.get(
                                "notes"
                            )
                            or ""
                        ),
                        key=(
                            "plan_notes_"
                            f"{item['id']}"
                        ),
                    )

                    save_plan = st.form_submit_button(
                        "Save plan",
                        width="stretch",
                    )

                if save_plan:
                    try:
                        update_build_plan_item(
                            client,
                            item["id"],
                            {
                                "status": edit_status,
                                "priority": edit_priority,
                                "estimated_cost_gbp": (
                                    _optional_money(
                                        edit_cost,
                                        "Estimated cost",
                                    )
                                ),
                                "target_date": (
                                    edit_target.isoformat()
                                    if edit_target
                                    else None
                                ),
                                "compatibility_status": (
                                    compatibility_status
                                ),
                                "compatibility_notes": (
                                    compatibility_notes.strip()
                                    or None
                                ),
                                "notes": (
                                    edit_notes.strip()
                                    or None
                                ),
                            },
                        )
                    except ValueError as error:
                        st.warning(
                            str(error)
                        )
                    except Exception as error:
                        st.error(
                            "VCG could not update the build plan."
                        )
                        log_ui_exception(error)
                    else:
                        st.rerun()

                st.markdown(
                    "#### Complete physical change"
                )

                with st.form(
                    f"complete_plan_{item['id']}"
                ):
                    completed_at = st.date_input(
                        "Completed date",
                        value=date.today(),
                        key=(
                            "plan_completed_date_"
                            f"{item['id']}"
                        ),
                    )
                    mileage = st.text_input(
                        "Vehicle mileage",
                        value=str(
                            int(
                                vehicle.get(
                                    "mileage"
                                )
                                or 0
                            )
                        ),
                        key=(
                            "plan_mileage_"
                            f"{item['id']}"
                        ),
                    )
                    actual_cost = st.text_input(
                        "Actual cost (£)",
                        placeholder="Optional",
                        key=(
                            "plan_actual_cost_"
                            f"{item['id']}"
                        ),
                    )
                    completion_notes = st.text_area(
                        "Completion notes",
                        placeholder=(
                            "Fitment, setup, findings or removal notes"
                        ),
                        key=(
                            "plan_completion_notes_"
                            f"{item['id']}"
                        ),
                    )

                    incompatible_install = (
                        action == "install"
                        and item.get(
                            "compatibility_status"
                        )
                        == "incompatible"
                    )

                    complete_change = st.form_submit_button(
                        (
                            "Mark installed"
                            if action == "install"
                            else "Mark removed"
                        ),
                        type="primary",
                        disabled=incompatible_install,
                        width="stretch",
                    )

                if (
                    action == "install"
                    and item.get(
                        "compatibility_status"
                    )
                    == "incompatible"
                ):
                    st.caption(
                        "Resolve the incompatible status before marking "
                        "this part installed."
                    )

                if complete_change:
                    try:
                        complete_build_plan_item(
                            client,
                            item["id"],
                            completed_at,
                            mileage=(
                                _optional_mileage(
                                    mileage
                                )
                            ),
                            actual_cost_gbp=(
                                _optional_money(
                                    actual_cost,
                                    "Actual cost",
                                )
                            ),
                            notes=completion_notes,
                        )
                    except ValueError as error:
                        st.warning(
                            str(error)
                        )
                    except Exception as error:
                        st.error(
                            "VCG could not complete the physical build change."
                        )
                        log_ui_exception(error)
                    else:
                        st.rerun()

                confirm_cancel = st.checkbox(
                    "Confirm plan cancellation",
                    key=(
                        "plan_cancel_confirm_"
                        f"{item['id']}"
                    ),
                )

                if st.button(
                    "Cancel plan item",
                    key=(
                        "plan_cancel_"
                        f"{item['id']}"
                    ),
                    disabled=(
                        not confirm_cancel
                    ),
                    width="stretch",
                ):
                    try:
                        cancel_build_plan_item(
                            client,
                            item["id"],
                            notes=(
                                "Cancelled from Build Planner."
                            ),
                        )
                    except Exception as error:
                        st.error(
                            "VCG could not cancel the build-plan item."
                        )
                        log_ui_exception(error)
                    else:
                        st.rerun()

            st.divider()

    with add_tab:
        install_tab, remove_tab = st.tabs(
            [
                "Plan installation",
                "Plan removal",
            ]
        )

        with install_tab:
            if not root_systems:
                st.warning(
                    "No digital-twin systems are available."
                )
            else:
                system_ids = [
                    str(
                        system[
                            "id"
                        ]
                    )
                    for system in root_systems
                ]
                system_lookup = {
                    str(
                        system[
                            "id"
                        ]
                    ): system
                    for system in root_systems
                }

                with st.form(
                    "add_install_plan",
                    clear_on_submit=True,
                ):
                    name = st.text_input(
                        "Part / modification",
                        placeholder="e.g. Skunk2 camshafts",
                    )
                    parent_system_id = st.selectbox(
                        "Vehicle system",
                        system_ids,
                        format_func=lambda system_id: (
                            system_lookup[
                                system_id
                            ][
                                "name"
                            ]
                        ),
                    )
                    plan_status = st.selectbox(
                        "Plan state",
                        PLAN_STATUSES,
                        index=1,
                    )
                    priority = st.selectbox(
                        "Priority",
                        PRIORITIES,
                        index=1,
                    )
                    origin = st.selectbox(
                        "Origin",
                        [
                            "Aftermarket",
                            "OEM / replacement",
                            "Unknown",
                        ],
                    )
                    manufacturer = st.text_input(
                        "Manufacturer",
                        placeholder="Optional",
                    )
                    part_number = st.text_input(
                        "Part number",
                        placeholder="Optional",
                    )
                    weight = st.text_input(
                        "Component weight (kg)",
                        placeholder="Optional — do not guess",
                    )
                    estimated_cost = st.text_input(
                        "Estimated total cost (£)",
                        placeholder="Optional",
                    )
                    compatibility_status = st.selectbox(
                        "Compatibility status",
                        COMPATIBILITY_STATUSES,
                        index=0,
                        help=(
                            "Leave Unknown until fitment is actually verified."
                        ),
                    )
                    compatibility_notes = st.text_area(
                        "Compatibility notes",
                        placeholder=(
                            "Supporting parts, tuning, clearance, evidence..."
                        ),
                    )
                    target_date = st.date_input(
                        "Target date",
                        value=None,
                    )
                    notes = st.text_area(
                        "Plan notes",
                        placeholder=(
                            "Reason, seller/source, setup goal..."
                        ),
                    )

                    add_install = st.form_submit_button(
                        "Add installation plan",
                        type="primary",
                        width="stretch",
                    )

                if add_install:
                    if not name.strip():
                        st.warning(
                            "Enter a part or modification."
                        )
                    else:
                        origin_map = {
                            "Aftermarket": False,
                            "OEM / replacement": True,
                            "Unknown": None,
                        }

                        try:
                            create_build_plan_install(
                                client,
                                vehicle["id"],
                                parent_system_id,
                                name.strip(),
                                manufacturer=(
                                    manufacturer.strip()
                                    or None
                                ),
                                part_number=(
                                    part_number.strip()
                                    or None
                                ),
                                weight_kg=(
                                    _optional_weight(
                                        weight
                                    )
                                ),
                                is_oem=origin_map[
                                    origin
                                ],
                                plan_status=plan_status,
                                priority=priority,
                                estimated_cost_gbp=(
                                    _optional_money(
                                        estimated_cost,
                                        "Estimated cost",
                                    )
                                ),
                                compatibility_status=(
                                    compatibility_status
                                ),
                                compatibility_notes=(
                                    compatibility_notes.strip()
                                    or None
                                ),
                                target_date=target_date,
                                notes=(
                                    notes.strip()
                                    or None
                                ),
                            )
                        except ValueError as error:
                            st.warning(
                                str(error)
                            )
                        except Exception as error:
                            st.error(
                                "VCG could not create the installation plan."
                            )
                            log_ui_exception(error)
                        else:
                            st.rerun()

        with remove_tab:
            active_removal_ids = {
                str(
                    item.get(
                        "component_id"
                    )
                )
                for item in snapshot["removals"]
            }

            removable = [
                component
                for component in snapshot[
                    "current_installed"
                ]
                if str(component["id"])
                not in active_removal_ids
            ]

            if not removable:
                st.caption(
                    "No installed components are available for a new removal plan."
                )
            else:
                removal_ids = [
                    str(
                        component[
                            "id"
                        ]
                    )
                    for component in removable
                ]
                removal_lookup = {
                    str(
                        component[
                            "id"
                        ]
                    ): component
                    for component in removable
                }

                with st.form(
                    "add_removal_plan",
                    clear_on_submit=True,
                ):
                    component_id = st.selectbox(
                        "Installed component",
                        removal_ids,
                        format_func=lambda item_id: (
                            removal_lookup[
                                item_id
                            ][
                                "name"
                            ]
                        ),
                    )
                    removal_status = st.selectbox(
                        "Plan state",
                        PLAN_STATUSES,
                        index=1,
                        key="removal_status",
                    )
                    removal_priority = st.selectbox(
                        "Priority",
                        PRIORITIES,
                        index=1,
                        key="removal_priority",
                    )
                    removal_cost = st.text_input(
                        "Estimated removal cost (£)",
                        placeholder="Optional",
                    )
                    removal_target = st.date_input(
                        "Target date",
                        value=None,
                        key="removal_target",
                    )
                    removal_notes = st.text_area(
                        "Removal notes",
                        placeholder=(
                            "Reason, replacement dependency, etc."
                        ),
                    )

                    add_removal = st.form_submit_button(
                        "Add removal plan",
                        type="primary",
                        width="stretch",
                    )

                if add_removal:
                    try:
                        create_build_plan_removal(
                            client,
                            component_id,
                            plan_status=(
                                removal_status
                            ),
                            priority=(
                                removal_priority
                            ),
                            estimated_cost_gbp=(
                                _optional_money(
                                    removal_cost,
                                    "Estimated removal cost",
                                )
                            ),
                            target_date=(
                                removal_target
                            ),
                            notes=(
                                removal_notes.strip()
                                or None
                            ),
                        )
                    except ValueError as error:
                        st.warning(
                            str(error)
                        )
                    except Exception as error:
                        st.error(
                            "VCG could not create the removal plan."
                        )
                        log_ui_exception(error)
                    else:
                        st.rerun()

    with history_tab:
        history = (
            snapshot["completed_items"]
            + snapshot["cancelled_items"]
        )

        history = sorted(
            history,
            key=lambda item: str(
                item.get("completed_at")
                or item.get("updated_at")
                or ""
            ),
            reverse=True,
        )

        if not history:
            st.caption(
                "No completed or cancelled build-plan items yet."
            )

        for item in history:
            component_name = _component_name(
                item,
                component_lookup,
            )

            st.markdown(
                f"**{str(item.get('action', 'change')).title()}: "
                f"{component_name}**"
            )

            meta = [
                str(
                    item.get(
                        "status",
                        "unknown",
                    )
                ).title()
            ]

            if item.get("actual_cost_gbp") is not None:
                meta.append(
                    f"Actual £{float(item['actual_cost_gbp']):,.2f}"
                )
            elif item.get("estimated_cost_gbp") is not None:
                meta.append(
                    f"Estimated £{float(item['estimated_cost_gbp']):,.2f}"
                )

            if item.get("completed_at"):
                meta.append(
                    str(
                        item[
                            "completed_at"
                        ]
                    )[:10]
                )

            st.caption(
                " · ".join(meta)
            )

            if item.get("notes"):
                st.write(
                    item["notes"]
                )

            st.divider()
