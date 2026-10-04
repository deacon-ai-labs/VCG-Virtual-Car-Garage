import unittest
from pathlib import Path


class TestM21V0ProductSimplification(unittest.TestCase):

    def setUp(self):
        self.app_source = Path(
            "app.py"
        ).read_text(
            encoding="utf-8"
        )

        self.nav_source = Path(
            "workspace_navigation.py"
        ).read_text(
            encoding="utf-8"
        )

        self.twin_source = Path(
            "virtual_twin_v0_ui.py"
        ).read_text(
            encoding="utf-8"
        )

    def test_virtual_twin_is_the_primary_vehicle_route(self):
        self.assertIn(
            'if workspace_mode == "Virtual Twin":',
            self.app_source,
        )
        self.assertNotIn(
            'if workspace_mode == "Vehicle Home":',
            self.app_source,
        )
        self.assertNotIn(
            "render_vehicle_command_deck(",
            self.app_source,
        )

    def test_only_twin_and_ai_are_persistent_destinations(self):
        self.assertIn(
            '"name": "Virtual Twin"',
            self.nav_source,
        )
        self.assertIn(
            '"name": "Garage AI"',
            self.nav_source,
        )

        primary_block = self.nav_source.split(
            "PRIMARY_WORKSPACES =",
            1,
        )[1].split(
            "CONTEXTUAL_WORKSPACES =",
            1,
        )[0]

        self.assertNotIn(
            "Diagnostics",
            primary_block,
        )
        self.assertNotIn(
            "Maintenance OS",
            primary_block,
        )
        self.assertNotIn(
            "Build Planner",
            primary_block,
        )

    def test_advanced_capabilities_remain_contextually_reachable(self):
        for workspace in (
            "Virtual Workshop",
            "Diagnostics",
            "Maintenance OS",
            "Build Planner",
        ):
            self.assertIn(
                f'if workspace_mode == "{workspace}":',
                self.app_source,
            )

        for action in (
            "Inspect",
            "Maintain",
            "Diagnose",
            "Modify",
            "AI",
        ):
            self.assertIn(
                f'"{action}"',
                self.twin_source,
            )

    def test_twin_is_car_first_not_dashboard_first(self):
        self.assertIn(
            "vcg_twin_hero",
            self.twin_source,
        )
        self.assertIn(
            "OWNED TWIN",
            self.twin_source,
        )
        self.assertNotIn(
            "st.tabs(",
            self.twin_source,
        )


if __name__ == "__main__":
    unittest.main()
