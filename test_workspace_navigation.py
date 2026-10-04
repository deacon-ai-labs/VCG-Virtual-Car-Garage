import unittest

from workspace_navigation import (
    allowed_workspace_names,
    contextual_badges,
    normalize_workspace,
    primary_workspace_names,
    workspace_state_key,
)


class TestWorkspaceNavigation(unittest.TestCase):

    def test_virtual_twin_is_default_workspace(self):
        self.assertEqual(
            normalize_workspace(
                None
            ),
            "Virtual Twin",
        )

    def test_legacy_vehicle_home_migrates_to_virtual_twin(self):
        self.assertEqual(
            normalize_workspace(
                "Vehicle Home"
            ),
            "Virtual Twin",
        )

    def test_contextual_workspace_is_preserved_for_internal_navigation(self):
        self.assertEqual(
            normalize_workspace(
                "Diagnostics"
            ),
            "Diagnostics",
        )

    def test_primary_navigation_is_intentionally_small(self):
        self.assertEqual(
            primary_workspace_names(),
            (
                "Virtual Twin",
                "Garage AI",
            ),
        )

    def test_contextual_tools_remain_available_under_the_twin(self):
        names = allowed_workspace_names()

        self.assertIn(
            "Virtual Workshop",
            names,
        )
        self.assertIn(
            "Diagnostics",
            names,
        )
        self.assertIn(
            "Maintenance OS",
            names,
        )
        self.assertIn(
            "Build Planner",
            names,
        )

    def test_badges_use_live_contextual_workload_counts(self):
        badges = contextual_badges(
            {
                "pending_count": 2,
            },
            {
                "active_case_count": 1,
            },
            {
                "active_count": 3,
            },
        )

        self.assertEqual(
            badges[
                "Maintenance OS"
            ],
            2,
        )
        self.assertEqual(
            badges[
                "Diagnostics"
            ],
            1,
        )
        self.assertEqual(
            badges[
                "Build Planner"
            ],
            3,
        )

    def test_state_key_is_vehicle_scoped(self):
        self.assertEqual(
            workspace_state_key(
                2
            ),
            "vehicle_workspace_mode_2",
        )


if __name__ == "__main__":
    unittest.main()
