import unittest

from build_planner import (
    build_plan_snapshot,
    format_build_plan_context,
)


class TestBuildPlanner(unittest.TestCase):

    def test_snapshot_keeps_current_and_planned_separate(self):
        components = [
            {
                "id": "installed",
                "component_type": "component",
                "name": "Current exhaust",
                "system_key": "exhaust",
                "lifecycle_status": "installed",
                "weight_kg": 10,
                "quantity": 1,
            },
            {
                "id": "planned",
                "component_type": "component",
                "name": "New exhaust",
                "system_key": "exhaust",
                "lifecycle_status": "planned",
                "weight_kg": 7,
                "quantity": 1,
            },
        ]

        plans = [
            {
                "component_id": "planned",
                "action": "install",
                "status": "planned",
                "estimated_cost_gbp": "500",
                "compatibility_status": "needs_review",
            },
            {
                "component_id": "installed",
                "action": "remove",
                "status": "planned",
                "estimated_cost_gbp": "50",
            },
        ]

        snapshot = build_plan_snapshot(
            plans,
            components,
        )

        self.assertEqual(
            snapshot["current_installed_count"],
            1,
        )
        self.assertEqual(
            snapshot["active_count"],
            2,
        )
        self.assertEqual(
            snapshot["estimated_cost_gbp"],
            550.0,
        )
        self.assertEqual(
            snapshot["known_weight_delta_kg"],
            -3.0,
        )
        self.assertEqual(
            snapshot["compatibility_review_count"],
            1,
        )

    def test_unknown_weights_are_not_invented(self):
        snapshot = build_plan_snapshot(
            [
                {
                    "component_id": "planned",
                    "action": "install",
                    "status": "wishlist",
                }
            ],
            [
                {
                    "id": "planned",
                    "component_type": "component",
                    "name": "Unknown weight part",
                    "lifecycle_status": "planned",
                    "weight_kg": None,
                }
            ],
        )

        self.assertEqual(
            snapshot["known_weight_delta_kg"],
            0.0,
        )
        self.assertEqual(
            snapshot["unknown_weight_actions"],
            1,
        )

    def test_ai_context_labels_future_changes(self):
        context = format_build_plan_context(
            [
                {
                    "component_id": "planned",
                    "action": "install",
                    "status": "planned",
                    "estimated_cost_gbp": "500",
                    "compatibility_status": "unknown",
                    "compatibility_notes": "Needs valve-train check",
                }
            ],
            [
                {
                    "id": "planned",
                    "component_type": "component",
                    "name": "Camshafts",
                    "system_key": "engine",
                    "lifecycle_status": "planned",
                    "weight_kg": 4.0,
                }
            ],
        )

        self.assertIn(
            "action=install",
            context,
        )
        self.assertIn(
            "plan_status=planned",
            context,
        )
        self.assertIn(
            "compatibility=unknown",
            context,
        )
        self.assertIn(
            "Needs valve-train check",
            context,
        )


if __name__ == "__main__":
    unittest.main()
