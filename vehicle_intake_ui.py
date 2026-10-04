from __future__ import annotations

import streamlit as st

from database import (
    add_vehicle,
)
from vehicle_intake import (
    VEHICLE_SYSTEMS,
    intake_snapshot,
    normalize_component_candidate,
    normalize_registration,
    normalize_vin,
)
from vehicle_intake_ai import (
    extract_modification_candidates,
)
from vehicle_intake_repository import (
    approve_component_candidate,
    create_evidence_record,
    create_intake_candidate,
    delete_evidence,
    mark_intake_complete,
    reject_intake_candidate,
    save_uploaded_evidence,
    update_intake_candidate,
)


EVIDENCE_TYPES = (
    "photo",
    "invoice",
    "receipt",
    "document",
    "dyno",
    "obd",
    "service",
    "other",
)


def render_new_vehicle_intake_form(
    client,
    owner_id: str,
) -> dict | None:
    """Create the identity shell for a new Twin."""

    st.caption(
        "Start with what you know. Registration/VIN lookup providers "
        "can plug into this intake later; V0 always keeps a manual fallback."
    )

    with st.form(
        "new_vehicle_intake_form",
        clear_on_submit=True,
    ):
        profile_name = st.text_input(
            "Car name",
            placeholder="My EP3",
        )

        id_left, id_right = st.columns(
            2
        )

        with id_left:
            registration = st.text_input(
                "Registration",
                placeholder="Optional",
            )

        with id_right:
            vin = st.text_input(
                "VIN",
                placeholder="Optional",
            )

        manufacturer = st.text_input(
            "Manufacturer",
            placeholder="Honda",
        )

        model = st.text_input(
            "Model / variant",
            placeholder="Civic Type R EP3",
        )

        year_col, mileage_col = st.columns(
            2
        )

        with year_col:
            year = st.number_input(
                "Year",
                min_value=1900,
                max_value=2100,
                step=1,
                value=2004,
            )

        with mileage_col:
            mileage = st.number_input(
                "Mileage",
                min_value=0,
                step=1000,
                value=0,
            )

        engine = st.text_input(
            "Engine",
            placeholder="2.0-litre K20A2",
        )

        submitted = st.form_submit_button(
            "Create Twin →",
            type="primary",
            width="stretch",
        )

    if not submitted:
        return None

    required = {
        "Car name": profile_name,
        "Manufacturer": manufacturer,
        "Model / variant": model,
        "Engine": engine,
    }

    missing = [
        label
        for label, value in required.items()
        if not value.strip()
    ]

    if missing:
        st.warning(
            "Please complete: "
            + ", ".join(
                missing
            )
        )
        return None

    try:
        return add_vehicle(
            client,
            owner_id,
            {
                "profile_name": profile_name.strip(),
                "manufacturer": manufacturer.strip(),
                "model": model.strip(),
                "year": int(
                    year
                ),
                "engine": engine.strip(),
                "mileage": int(
                    mileage
                ),
                "modifications": "",
                "registration": normalize_registration(
                    registration
                ),
                "vin": normalize_vin(
                    vin
                ),
                "intake_status": "in_progress",
            },
        )
    except Exception as error:
        st.error(
            "VCG could not create the vehicle Twin."
        )
        st.exception(
            error
        )
        return None


def _vehicle_description(
    vehicle: dict,
) -> str:
    return (
        f"{vehicle.get('year', '')} "
        f"{vehicle.get('manufacturer', '')} "
        f"{vehicle.get('model', '')}; "
        f"engine={vehicle.get('engine', '')}"
    )


def _evidence_label(
    evidence: dict,
) -> str:
    return (
        f"{evidence.get('title') or 'Evidence'} "
        f"({str(evidence.get('evidence_type') or 'other').title()})"
    )


def _render_evidence_section(
    client,
    owner_id: str,
    vehicle: dict,
    evidence: list[dict],
    candidates: list[dict],
) -> None:
    st.markdown(
        "#### Evidence"
    )
    st.caption(
        "Receipts, invoices, photos and documents stay private. "
        "Uploading evidence does not change the Twin by itself."
    )

    with st.form(
        f"evidence_upload_{vehicle['id']}",
        clear_on_submit=True,
    ):
        evidence_type = st.selectbox(
            "Evidence type",
            EVIDENCE_TYPES,
            format_func=lambda value: value.replace(
                "_",
                " ",
            ).title(),
        )

        title = st.text_input(
            "Evidence title",
            placeholder="BC Racing invoice",
        )

        notes = st.text_area(
            "Notes",
            placeholder="Optional context",
        )

        upload = st.file_uploader(
            "File",
            type=[
                "jpg",
                "jpeg",
                "png",
                "webp",
                "pdf",
                "txt",
                "csv",
                "json",
            ],
        )

        submitted = st.form_submit_button(
            "Save evidence",
            width="stretch",
        )

    if submitted:
        if upload is None:
            st.warning(
                "Choose a file to upload."
            )
        elif not title.strip():
            st.warning(
                "Give the evidence a title."
            )
        else:
            try:
                save_uploaded_evidence(
                    client=client,
                    owner_id=owner_id,
                    vehicle_id=vehicle[
                        "id"
                    ],
                    evidence_type=evidence_type,
                    title=title.strip(),
                    filename=upload.name,
                    file_bytes=upload.getvalue(),
                    content_type=(
                        upload.type
                        or "application/octet-stream"
                    ),
                    notes=(
                        notes.strip()
                        or None
                    ),
                )
            except Exception as error:
                st.error(
                    "VCG could not save this evidence."
                )
                st.exception(
                    error
                )
            else:
                st.rerun()

    protected_evidence_ids = {
        str(
            candidate.get(
                "evidence_id"
            )
        )
        for candidate in candidates
        if (
            candidate.get(
                "evidence_id"
            )
            and candidate.get(
                "review_status"
            )
            == "approved"
        )
    }

    if evidence:
        for item in evidence:
            left, right = st.columns(
                [5, 1]
            )

            with left:
                st.markdown(
                    f"**{item.get('title') or 'Evidence'}**"
                )
                st.caption(
                    (
                        str(
                            item.get(
                                "evidence_type"
                            )
                            or "other"
                        ).title()
                        + (
                            f" · {item.get('original_filename')}"
                            if item.get(
                                "original_filename"
                            )
                            else ""
                        )
                    )
                )

            with right:
                is_protected = (
                    str(
                        item[
                            "id"
                        ]
                    )
                    in protected_evidence_ids
                )

                if is_protected:
                    st.caption(
                        "Used by Twin"
                    )

                if st.button(
                    "Delete",
                    key=(
                        "delete_evidence_"
                        f"{item['id']}"
                    ),
                    disabled=is_protected,
                    width="stretch",
                ):
                    try:
                        delete_evidence(
                            client,
                            item,
                        )
                    except Exception as error:
                        st.error(
                            "VCG could not delete this evidence."
                        )
                        st.exception(
                            error
                        )
                    else:
                        st.rerun()


def _render_modification_capture(
    client,
    owner_id: str,
    vehicle: dict,
    evidence: list[dict],
) -> None:
    st.markdown(
        "#### Tell VCG what is modified"
    )
    st.caption(
        "Describe what is physically fitted now. VCG will propose "
        "structured components, but nothing is added until you approve it."
    )

    with st.form(
        f"analyse_intake_modifications_{vehicle['id']}",
        clear_on_submit=True,
    ):
        modification_text = st.text_area(
            "Current modifications",
            placeholder=(
                "Example: BC Racing coilovers, K100 ECU, "
                "4-2-1 manifold and a cat-back exhaust."
            ),
        )

        analyse = st.form_submit_button(
            "Analyse modifications",
            type="primary",
            width="stretch",
        )

    if analyse:
        if not modification_text.strip():
            st.warning(
                "Describe at least one current modification."
            )
        else:
            try:
                extracted = extract_modification_candidates(
                    modification_text,
                    _vehicle_description(
                        vehicle
                    ),
                )

                if not extracted:
                    st.info(
                        "No clearly installed components were extracted."
                    )
                else:
                    source_evidence = create_evidence_record(
                        client=client,
                        owner_id=owner_id,
                        vehicle_id=vehicle[
                            "id"
                        ],
                        evidence_data={
                            "evidence_type": "other",
                            "title": "Owner modification description",
                            "source_kind": "manual_entry",
                            "notes": modification_text.strip(),
                        },
                    )

                    for candidate in extracted:
                        confidence = candidate.pop(
                            "confidence",
                            "unknown",
                        )

                        create_intake_candidate(
                            client=client,
                            owner_id=owner_id,
                            vehicle_id=vehicle[
                                "id"
                            ],
                            evidence_id=source_evidence[
                                "id"
                            ],
                            candidate_kind="component",
                            source_kind="ai_extraction",
                            source_reference=(
                                "Owner modification description"
                            ),
                            confidence=confidence,
                            payload=candidate,
                        )
            except Exception as error:
                st.error(
                    "VCG could not analyse the modification description."
                )
                st.exception(
                    error
                )
            else:
                st.rerun()

    st.markdown(
        "##### Add a component manually"
    )

    with st.form(
        f"manual_candidate_{vehicle['id']}",
        clear_on_submit=True,
    ):
        name = st.text_input(
            "Component",
            placeholder="BC Racing Coilovers",
        )

        system_key = st.selectbox(
            "Vehicle system",
            [
                key
                for key, _label in VEHICLE_SYSTEMS
            ],
            format_func=lambda key: dict(
                VEHICLE_SYSTEMS
            )[
                key
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

        evidence_options = [
            ""
        ] + [
            str(
                item[
                    "id"
                ]
            )
            for item in evidence
        ]

        evidence_lookup = {
            str(
                item[
                    "id"
                ]
            ): item
            for item in evidence
        }

        evidence_id = st.selectbox(
            "Supporting evidence",
            evidence_options,
            format_func=lambda value: (
                "None"
                if not value
                else _evidence_label(
                    evidence_lookup[
                        value
                    ]
                )
            ),
        )

        notes = st.text_area(
            "Notes",
            placeholder="Only record what you know.",
        )

        submitted = st.form_submit_button(
            "Add for review",
            width="stretch",
        )

    if submitted:
        try:
            normalized = normalize_component_candidate(
                {
                    "name": name,
                    "system_key": system_key,
                    "manufacturer": (
                        manufacturer
                        or None
                    ),
                    "part_number": (
                        part_number
                        or None
                    ),
                    "notes": (
                        notes
                        or None
                    ),
                    "confidence": (
                        "medium"
                        if evidence_id
                        else "unknown"
                    ),
                }
            )

            confidence = normalized.pop(
                "confidence"
            )

            create_intake_candidate(
                client=client,
                owner_id=owner_id,
                vehicle_id=vehicle[
                    "id"
                ],
                candidate_kind="component",
                source_kind=(
                    "evidence"
                    if evidence_id
                    else "user"
                ),
                source_reference=(
                    _evidence_label(
                        evidence_lookup[
                            evidence_id
                        ]
                    )
                    if evidence_id
                    else "Owner confirmation"
                ),
                evidence_id=(
                    evidence_id
                    or None
                ),
                confidence=confidence,
                payload=normalized,
            )
        except Exception as error:
            st.error(
                "VCG could not create the component candidate."
            )
            st.exception(
                error
            )
        else:
            st.rerun()


def _render_candidate_review(
    client,
    vehicle: dict,
    candidates: list[dict],
) -> None:
    pending = [
        item
        for item in candidates
        if item.get(
            "review_status"
        )
        == "pending"
    ]

    st.markdown(
        "#### Review proposed Twin changes"
    )

    if not pending:
        st.caption(
            "No proposed changes are waiting for review."
        )
        return

    systems = [
        key
        for key, _label in VEHICLE_SYSTEMS
    ]
    system_labels = dict(
        VEHICLE_SYSTEMS
    )

    for candidate in pending:
        payload = candidate.get(
            "payload"
        ) or {}

        title = payload.get(
            "name"
        ) or "Unnamed component"

        with st.container(
            border=True,
        ):
            st.markdown(
                f"**{title}** · {candidate.get('confidence', 'unknown')} confidence"
            )

            current_system = payload.get(
                "system_key"
            )

            if current_system not in systems:
                current_system = systems[0]

            with st.form(
                f"review_candidate_{candidate['id']}"
            ):
                name = st.text_input(
                    "Component",
                    value=title,
                )

                system_key = st.selectbox(
                    "Vehicle system",
                    systems,
                    index=systems.index(
                        current_system
                    ),
                    format_func=lambda key: system_labels[
                        key
                    ],
                )

                manufacturer = st.text_input(
                    "Manufacturer",
                    value=(
                        payload.get(
                            "manufacturer"
                        )
                        or ""
                    ),
                )

                part_number = st.text_input(
                    "Part number",
                    value=(
                        payload.get(
                            "part_number"
                        )
                        or ""
                    ),
                )

                position = st.text_input(
                    "Position",
                    value=(
                        payload.get(
                            "position"
                        )
                        or ""
                    ),
                    placeholder="Optional",
                )

                notes = st.text_area(
                    "Notes",
                    value=(
                        payload.get(
                            "notes"
                        )
                        or ""
                    ),
                )

                st.caption(
                    "Source: "
                    + str(
                        candidate.get(
                            "source_reference"
                        )
                        or candidate.get(
                            "source_kind"
                        )
                        or "Unknown"
                    )
                )

                approve_col, reject_col = st.columns(
                    2
                )

                with approve_col:
                    approve = st.form_submit_button(
                        "Approve & add to Twin",
                        type="primary",
                        width="stretch",
                    )

                with reject_col:
                    reject = st.form_submit_button(
                        "Reject",
                        width="stretch",
                    )

            if approve:
                try:
                    normalized = normalize_component_candidate(
                        {
                            "name": name,
                            "system_key": system_key,
                            "manufacturer": (
                                manufacturer
                                or None
                            ),
                            "part_number": (
                                part_number
                                or None
                            ),
                            "position": (
                                position
                                or None
                            ),
                            "notes": (
                                notes
                                or None
                            ),
                            "confidence": candidate.get(
                                "confidence",
                                "unknown",
                            ),
                        }
                    )

                    confidence = normalized.pop(
                        "confidence"
                    )

                    update_intake_candidate(
                        client,
                        candidate[
                            "id"
                        ],
                        normalized,
                        confidence,
                    )

                    approve_component_candidate(
                        client,
                        candidate[
                            "id"
                        ],
                    )
                except Exception as error:
                    st.error(
                        "VCG could not approve this Twin change."
                    )
                    st.exception(
                        error
                    )
                else:
                    st.rerun()

            if reject:
                try:
                    reject_intake_candidate(
                        client,
                        candidate[
                            "id"
                        ],
                    )
                except Exception as error:
                    st.error(
                        "VCG could not reject this candidate."
                    )
                    st.exception(
                        error
                    )
                else:
                    st.rerun()


def render_vehicle_intake_panel(
    client,
    owner_id: str,
    vehicle: dict,
    evidence: list[dict],
    candidates: list[dict],
) -> None:
    snapshot = intake_snapshot(
        vehicle,
        evidence,
        candidates,
    )

    is_active_intake = (
        snapshot[
            "status"
        ]
        != "complete"
    )

    title = (
        "Finish setting up your Twin"
        if is_active_intake
        else "Improve Twin data"
    )

    with st.expander(
        title,
        expanded=is_active_intake,
    ):
        st.caption(
            "VCG separates evidence and proposed facts from the canonical "
            "Twin. You approve every change."
        )

        identity_parts = [
            (
                f"Registration: {snapshot['registration']}"
                if snapshot[
                    "registration"
                ]
                else "Registration: not provided"
            ),
            (
                f"VIN: {snapshot['vin']}"
                if snapshot[
                    "vin"
                ]
                else "VIN: not provided"
            ),
        ]

        st.markdown(
            "**Vehicle identity**  \n"
            + " · ".join(
                identity_parts
            )
        )

        metric_a, metric_b, metric_c = st.columns(
            3
        )

        with metric_a:
            st.metric(
                "Evidence",
                snapshot[
                    "evidence_count"
                ],
                border=True,
            )

        with metric_b:
            st.metric(
                "Awaiting review",
                snapshot[
                    "pending_count"
                ],
                border=True,
            )

        with metric_c:
            st.metric(
                "Approved",
                snapshot[
                    "approved_count"
                ],
                border=True,
            )

        _render_evidence_section(
            client,
            owner_id,
            vehicle,
            evidence,
            candidates,
        )

        st.divider()

        _render_modification_capture(
            client,
            owner_id,
            vehicle,
            evidence,
        )

        st.divider()

        _render_candidate_review(
            client,
            vehicle,
            candidates,
        )

        if is_active_intake:
            st.divider()

            if snapshot[
                "pending_count"
            ]:
                st.caption(
                    "Review or reject all proposed changes before finishing setup."
                )
            elif st.button(
                "Finish Twin setup",
                key=(
                    "finish_vehicle_intake_"
                    f"{vehicle['id']}"
                ),
                type="primary",
                width="stretch",
            ):
                try:
                    mark_intake_complete(
                        client,
                        vehicle[
                            "id"
                        ],
                    )
                except Exception as error:
                    st.error(
                        "VCG could not finish this vehicle setup."
                    )
                    st.exception(
                        error
                    )
                else:
                    st.rerun()
