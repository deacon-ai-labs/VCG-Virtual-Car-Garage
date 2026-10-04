from __future__ import annotations


ACTIVE_CASE_STATUSES = {
    "open",
    "monitoring",
}


HYPOTHESIS_RANK = {
    "leading": 0,
    "possible": 1,
    "weakened": 2,
    "ruled_out": 3,
    "confirmed": 4,
}


def case_snapshot(
    case: dict,
    hypotheses: list[dict],
    checks: list[dict],
) -> dict:
    """Summarise one diagnostic investigation without inferring a diagnosis."""

    case_id = str(
        case["id"]
    )

    case_hypotheses = [
        hypothesis
        for hypothesis in hypotheses
        if str(
            hypothesis.get(
                "case_id"
            )
        )
        == case_id
    ]

    case_checks = [
        check
        for check in checks
        if str(
            check.get(
                "case_id"
            )
        )
        == case_id
    ]

    planned_checks = [
        check
        for check in case_checks
        if check.get(
            "status"
        )
        == "planned"
    ]

    completed_checks = [
        check
        for check in case_checks
        if check.get(
            "status"
        )
        == "completed"
    ]

    skipped_checks = [
        check
        for check in case_checks
        if check.get(
            "status"
        )
        == "skipped"
    ]

    hypothesis_lookup = {
        str(
            hypothesis[
                "id"
            ]
        ): hypothesis
        for hypothesis in case_hypotheses
    }

    def check_rank(
        check: dict,
    ) -> tuple:
        hypothesis = (
            hypothesis_lookup.get(
                str(
                    check.get(
                        "hypothesis_id"
                    )
                )
            )
            if check.get(
                "hypothesis_id"
            )
            else None
        )

        hypothesis_status = (
            hypothesis.get(
                "status"
            )
            if hypothesis
            else "possible"
        )

        return (
            HYPOTHESIS_RANK.get(
                hypothesis_status,
                5,
            ),
            check.get(
                "sort_order",
                0,
            ),
            check.get(
                "created_at",
                "",
            ),
            check.get(
                "title",
                "",
            ),
        )

    eligible_next_checks = [
        check
        for check in planned_checks
        if (
            check.get(
                "hypothesis_id"
            )
            is None
            or (
                hypothesis_lookup.get(
                    str(
                        check.get(
                            "hypothesis_id"
                        )
                    ),
                    {},
                ).get(
                    "status"
                )
                not in {
                    "ruled_out",
                    "confirmed",
                }
            )
        )
    ]

    next_check = (
        sorted(
            eligible_next_checks,
            key=check_rank,
        )[0]
        if eligible_next_checks
        else None
    )

    outcomes = {
        "supports": 0,
        "weakens": 0,
        "neutral": 0,
        "inconclusive": 0,
        "not_applicable": 0,
    }

    for check in completed_checks:
        outcome = check.get(
            "outcome"
        )

        if outcome in outcomes:
            outcomes[
                outcome
            ] += 1

    hypothesis_counts = {
        "possible": 0,
        "leading": 0,
        "weakened": 0,
        "ruled_out": 0,
        "confirmed": 0,
    }

    for hypothesis in case_hypotheses:
        status = hypothesis.get(
            "status"
        )

        if status in hypothesis_counts:
            hypothesis_counts[
                status
            ] += 1

    return {
        "hypotheses": case_hypotheses,
        "checks": case_checks,
        "planned_checks": planned_checks,
        "completed_checks": completed_checks,
        "skipped_checks": skipped_checks,
        "next_check": next_check,
        "hypothesis_counts": hypothesis_counts,
        "outcomes": outcomes,
        "hypothesis_count": len(
            case_hypotheses
        ),
        "planned_check_count": len(
            planned_checks
        ),
        "completed_check_count": len(
            completed_checks
        ),
        "evidence_count": len(
            completed_checks
        ),
    }


def diagnostic_vehicle_snapshot(
    cases: list[dict],
    hypotheses: list[dict],
    checks: list[dict],
) -> dict:
    """Summarise diagnostics for one vehicle."""

    active_cases = [
        case
        for case in cases
        if case.get(
            "status"
        )
        in ACTIVE_CASE_STATUSES
    ]

    resolved_cases = [
        case
        for case in cases
        if case.get(
            "status"
        )
        in {
            "resolved",
            "closed",
        }
    ]

    active_case_ids = {
        str(
            case[
                "id"
            ]
        )
        for case in active_cases
    }

    open_checks = [
        check
        for check in checks
        if (
            str(
                check.get(
                    "case_id"
                )
            )
            in active_case_ids
            and check.get(
                "status"
            )
            == "planned"
        )
    ]

    completed_checks = [
        check
        for check in checks
        if check.get(
            "status"
        )
        == "completed"
    ]

    confirmed_hypotheses = [
        hypothesis
        for hypothesis in hypotheses
        if hypothesis.get(
            "status"
        )
        == "confirmed"
    ]

    return {
        "active_cases": active_cases,
        "resolved_cases": resolved_cases,
        "active_case_count": len(
            active_cases
        ),
        "resolved_case_count": len(
            resolved_cases
        ),
        "open_check_count": len(
            open_checks
        ),
        "completed_check_count": len(
            completed_checks
        ),
        "confirmed_hypothesis_count": len(
            confirmed_hypotheses
        ),
    }


def _component_name(
    component_id,
    component_lookup: dict[str, dict],
) -> str:
    if component_id is None:
        return "Vehicle-level"

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


def format_diagnostic_context(
    cases: list[dict],
    hypotheses: list[dict],
    checks: list[dict],
    components: list[dict],
    focus_case_id: str | None = None,
) -> str:
    """Format bounded diagnostic records for Garage AI."""

    if not cases:
        return (
            "No diagnostic investigations are recorded for this vehicle."
        )

    component_lookup = {
        str(
            component[
                "id"
            ]
        ): component
        for component in components
    }

    active = [
        case
        for case in cases
        if case.get(
            "status"
        )
        in ACTIVE_CASE_STATUSES
    ]

    resolved = [
        case
        for case in cases
        if case.get(
            "status"
        )
        in {
            "resolved",
            "closed",
        }
    ]

    selected_cases = (
        active[:3]
        + resolved[:2]
    )

    if focus_case_id is not None:
        focused = next(
            (
                case
                for case in cases
                if str(
                    case.get(
                        "id"
                    )
                )
                == str(
                    focus_case_id
                )
            ),
            None,
        )

        if focused is not None:
            selected_cases = [
                focused,
                *[
                    case
                    for case in selected_cases
                    if str(
                        case.get(
                            "id"
                        )
                    )
                    != str(
                        focus_case_id
                    )
                ],
            ]

    lines = [
        (
            "Diagnostic records are investigation state, not proof. "
            "A hypothesis marked possible/leading/weakened is not a confirmed cause. "
            "A completed check records what was observed; its outcome describes "
            "how that check bears on a hypothesis, not an absolute diagnosis."
        )
    ]

    for case in selected_cases:
        case_id = str(
            case[
                "id"
            ]
        )

        lines.append(
            (
                f"CASE: {case.get('title') or 'Untitled'}; "
                f"status={case.get('status') or 'open'}; "
                f"priority={case.get('priority') or 'normal'}; "
                f"drive_risk={case.get('drive_risk') or 'unknown'}"
            )
        )

        lines.append(
            "  symptom="
            + str(
                case.get(
                    "symptom_description"
                )
                or "No symptom description"
            )
        )

        if case.get(
            "operating_conditions"
        ):
            lines.append(
                "  conditions="
                + str(
                    case[
                        "operating_conditions"
                    ]
                )
            )

        if case.get(
            "onset_mileage"
        ) is not None:
            lines.append(
                "  onset_mileage="
                + str(
                    case[
                        "onset_mileage"
                    ]
                )
            )

        if case.get(
            "resolution_summary"
        ):
            lines.append(
                "  recorded_resolution="
                + str(
                    case[
                        "resolution_summary"
                    ]
                )
            )

        case_hypotheses = [
            hypothesis
            for hypothesis in hypotheses
            if str(
                hypothesis.get(
                    "case_id"
                )
            )
            == case_id
        ]

        if case_hypotheses:
            lines.append(
                "  HYPOTHESES:"
            )

            for hypothesis in case_hypotheses[:8]:
                details = [
                    hypothesis.get(
                        "title"
                    )
                    or "Untitled hypothesis",
                    (
                        "status="
                        + str(
                            hypothesis.get(
                                "status"
                            )
                            or "possible"
                        )
                    ),
                    (
                        "component="
                        + _component_name(
                            hypothesis.get(
                                "component_id"
                            ),
                            component_lookup,
                        )
                    ),
                    (
                        "source="
                        + str(
                            hypothesis.get(
                                "source_kind"
                            )
                            or "user"
                        )
                    ),
                ]

                if hypothesis.get(
                    "rationale"
                ):
                    details.append(
                        "rationale="
                        + str(
                            hypothesis[
                                "rationale"
                            ]
                        )
                    )

                lines.append(
                    "    - "
                    + "; ".join(
                        details
                    )
                )
        else:
            lines.append(
                "  HYPOTHESES: none recorded"
            )

        case_checks = [
            check
            for check in checks
            if str(
                check.get(
                    "case_id"
                )
            )
            == case_id
        ]

        completed = [
            check
            for check in case_checks
            if check.get(
                "status"
            )
            == "completed"
        ][:10]

        planned = [
            check
            for check in case_checks
            if check.get(
                "status"
            )
            == "planned"
        ][:6]

        if completed:
            lines.append(
                "  COMPLETED CHECKS:"
            )

            for check in completed:
                details = [
                    check.get(
                        "title"
                    )
                    or "Untitled check",
                    (
                        "outcome="
                        + str(
                            check.get(
                                "outcome"
                            )
                            or "unknown"
                        )
                    ),
                    (
                        "finding="
                        + str(
                            check.get(
                                "finding"
                            )
                            or "No finding"
                        )
                    ),
                    (
                        "component="
                        + _component_name(
                            check.get(
                                "component_id"
                            ),
                            component_lookup,
                        )
                    ),
                ]

                if check.get(
                    "performed_mileage"
                ) is not None:
                    details.append(
                        "mileage="
                        + str(
                            check[
                                "performed_mileage"
                            ]
                        )
                    )

                lines.append(
                    "    - "
                    + "; ".join(
                        details
                    )
                )

        if planned:
            lines.append(
                "  PLANNED CHECKS:"
            )

            for check in planned:
                details = [
                    check.get(
                        "title"
                    )
                    or "Untitled check",
                    (
                        "type="
                        + str(
                            check.get(
                                "check_type"
                            )
                            or "inspection"
                        )
                    ),
                    (
                        "component="
                        + _component_name(
                            check.get(
                                "component_id"
                            ),
                            component_lookup,
                        )
                    ),
                ]

                if check.get(
                    "procedure"
                ):
                    details.append(
                        "procedure="
                        + str(
                            check[
                                "procedure"
                            ]
                        )
                    )

                if check.get(
                    "safety_notes"
                ):
                    details.append(
                        "safety="
                        + str(
                            check[
                                "safety_notes"
                            ]
                        )
                    )

                lines.append(
                    "    - "
                    + "; ".join(
                        details
                    )
                )

    return "\n".join(
        lines
    )
