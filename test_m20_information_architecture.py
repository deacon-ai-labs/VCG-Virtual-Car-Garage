import unittest
from pathlib import Path


class TestM20InformationArchitecture(unittest.TestCase):

    def setUp(self):
        self.app_source = Path(
            "app.py"
        ).read_text(
            encoding="utf-8"
        )

        self.theme_source = Path(
            "ui_theme.py"
        ).read_text(
            encoding="utf-8"
        )

    def test_vehicle_home_replaces_old_workspace_radio_as_primary_navigation(self):
        self.assertIn(
            "render_workspace_navigation(",
            self.app_source,
        )
        self.assertIn(
            'if workspace_mode == "Vehicle Home":',
            self.app_source,
        )
        self.assertNotIn(
            'st.radio(\n            "Vehicle workspace"',
            self.app_source,
        )

    def test_vehicle_settings_live_on_vehicle_home(self):
        home_index = self.app_source.index(
            'if workspace_mode == "Vehicle Home":'
        )
        settings_index = self.app_source.index(
            "render_vehicle_management(",
        )

        self.assertGreater(
            settings_index,
            home_index,
        )
        self.assertNotIn(
            "At a glance",
            self.app_source,
        )

    def test_conversations_are_scoped_to_garage_ai(self):
        self.assertIn(
            'if workspace_mode == "Garage AI":',
            self.app_source,
        )
        self.assertIn(
            "CONVERSATIONS",
            self.app_source,
        )
        self.assertIn(
            "Garage AI conversations appear here when the AI workspace is open.",
            self.app_source,
        )

    def test_long_workspaces_use_bounded_app_panes(self):
        self.assertIn(
            'key="vcg_home_scroll"',
            self.app_source,
        )
        self.assertIn(
            'key="vcg_workspace_scroll"',
            self.app_source,
        )
        self.assertIn(
            'key="vcg_workshop_scroll"',
            self.app_source,
        )
        self.assertIn(
            'key="vcg_diagnostics_scroll"',
            self.app_source,
        )

    def test_shell_styles_exist_for_command_deck_and_navigation(self):
        self.assertIn(
            ".vcg-command-deck",
            self.theme_source,
        )
        self.assertIn(
            ".st-key-vcg_workspace_nav",
            self.theme_source,
        )
        self.assertIn(
            ".vcg-home-hero",
            self.theme_source,
        )
        self.assertIn(
            ".st-key-vcg_home_scroll",
            self.theme_source,
        )


if __name__ == "__main__":
    unittest.main()
