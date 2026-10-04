import unittest

from workspace_navigation import (
    normalize_workspace,
    workspace_badges,
    workspace_names,
    workspace_state_key,
)


class TestWorkspaceNavigation(unittest.TestCase):

    def test_vehicle_home_is_default_workspace(self):
        self.assertEqual(
            normalize_workspace(
                None
            ),
            "Vehicle Home",
        )

    def test_known_workspace_is_preserved(self):
        self.assertEqual(
            normalize_workspace(
                "Diagnostics"
            ),
            "Diagnostics",
        )

    def test_workspace_names_include_core_vehicle_os_pages(self):
        names = workspace_names()

        self.assertIn(
            "Vehicle Home",
            names,
        )
        self.assertIn(
            "Garage AI",
            names,
        )
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

    def test_badges_use_live_workload_counts(self):
        badges = workspace_badges(
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
