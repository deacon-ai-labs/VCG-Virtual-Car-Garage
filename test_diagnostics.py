import unittest

from diagnostics import (
    case_snapshot,
    diagnostic_vehicle_snapshot,
    format_diagnostic_context,
)


class TestDiagnostics(unittest.TestCase):

    def test_case_snapshot_prioritises_check_for_leading_hypothesis(self):
        case = {
            "id": "case-1",
            "status": "open",
        }

        hypotheses = [
            {
                "id": "h-possible",
                "case_id": "case-1",
                "status": "possible",
            },
            {
                "id": "h-leading",
                "case_id": "case-1",
                "status": "leading",
            },
        ]

        checks = [
            {
                "id": "check-possible",
                "case_id": "case-1",
                "hypothesis_id": "h-possible",
                "status": "planned",
                "sort_order": 0,
                "title": "Possible check",
            },
            {
                "id": "check-leading",
                "case_id": "case-1",
                "hypothesis_id": "h-leading",
                "status": "planned",
                "sort_order": 5,
                "title": "Leading check",
            },
        ]

        snapshot = case_snapshot(
            case,
            hypotheses,
            checks,
        )

        self.assertEqual(
            snapshot["next_check"]["id"],
            "check-leading",
        )
        self.assertEqual(
            snapshot["planned_check_count"],
            2,
        )

    def test_next_check_ignores_ruled_out_hypothesis(self):
        snapshot = case_snapshot(
            {
                "id": "case-1",
            },
            [
                {
                    "id": "ruled-out",
                    "case_id": "case-1",
                    "status": "ruled_out",
                },
                {
                    "id": "possible",
                    "case_id": "case-1",
                    "status": "possible",
                },
            ],
            [
                {
                    "id": "stale",
                    "case_id": "case-1",
                    "hypothesis_id": "ruled-out",
                    "status": "planned",
                    "title": "Stale check",
                },
                {
                    "id": "useful",
                    "case_id": "case-1",
                    "hypothesis_id": "possible",
                    "status": "planned",
                    "title": "Useful check",
                },
            ],
        )

        self.assertEqual(
            snapshot["next_check"]["id"],
            "useful",
        )

    def test_completed_check_outcomes_are_counted_as_evidence(self):
        snapshot = case_snapshot(
            {
                "id": "case-1",
            },
            [],
            [
                {
                    "case_id": "case-1",
                    "status": "completed",
                    "outcome": "supports",
                },
                {
                    "case_id": "case-1",
                    "status": "completed",
                    "outcome": "inconclusive",
                },
            ],
        )

        self.assertEqual(
            snapshot["evidence_count"],
            2,
        )
        self.assertEqual(
            snapshot["outcomes"]["supports"],
            1,
        )
        self.assertEqual(
            snapshot["outcomes"]["inconclusive"],
            1,
        )

    def test_vehicle_snapshot_counts_active_cases_and_open_checks(self):
        snapshot = diagnostic_vehicle_snapshot(
            [
                {
                    "id": "open",
                    "status": "open",
                },
                {
                    "id": "resolved",
                    "status": "resolved",
                },
            ],
            [
                {
                    "case_id": "open",
                    "status": "confirmed",
                }
            ],
            [
                {
                    "case_id": "open",
                    "status": "planned",
                },
                {
                    "case_id": "open",
                    "status": "completed",
                },
            ],
        )

        self.assertEqual(
            snapshot["active_case_count"],
            1,
        )
        self.assertEqual(
            snapshot["resolved_case_count"],
            1,
        )
        self.assertEqual(
            snapshot["open_check_count"],
            1,
        )
        self.assertEqual(
            snapshot["completed_check_count"],
            1,
        )

    def test_focused_case_is_put_first_in_ai_context(self):
        context = format_diagnostic_context(
            [
                {
                    "id": "case-new",
                    "title": "Newer case",
                    "status": "open",
                    "priority": "normal",
                    "drive_risk": "unknown",
                    "symptom_description": "New",
                },
                {
                    "id": "case-focus",
                    "title": "Focused case",
                    "status": "open",
                    "priority": "normal",
                    "drive_risk": "unknown",
                    "symptom_description": "Focus",
                },
            ],
            [],
            [],
            [],
            focus_case_id="case-focus",
        )

        self.assertLess(
            context.index("CASE: Focused case"),
            context.index("CASE: Newer case"),
        )

    def test_ai_context_does_not_equate_leading_with_confirmed(self):
        context = format_diagnostic_context(
            [
                {
                    "id": "case-1",
                    "title": "Pull left",
                    "status": "open",
                    "priority": "high",
                    "drive_risk": "unknown",
                    "symptom_description": "Pulls left under braking",
                }
            ],
            [
                {
                    "id": "h-1",
                    "case_id": "case-1",
                    "title": "Binding brake",
                    "status": "leading",
                    "source_kind": "user",
                    "component_id": None,
                }
            ],
            [
                {
                    "case_id": "case-1",
                    "title": "Temperature check",
                    "status": "completed",
                    "outcome": "supports",
                    "finding": "Right side hotter",
                    "component_id": None,
                }
            ],
            [],
        )

        self.assertIn(
            "status=leading",
            context,
        )
        self.assertIn(
            "outcome=supports",
            context,
        )
        self.assertIn(
            "is not a confirmed cause",
            context,
        )


if __name__ == "__main__":
    unittest.main()
