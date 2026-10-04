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

    def test_primary_navigation_replaces_old_workspace_radio(self):
        self.assertIn(
            "render_primary_navigation(",
            self.app_source,
        )
        self.assertNotIn(
            'st.radio(\n            "Vehicle workspace"',
            self.app_source,
        )

    def test_vehicle_management_is_not_buried_in_garage_ai(self):
        twin_index = self.app_source.index(
            'if workspace_mode == "Virtual Twin":'
        )
        settings_index = self.app_source.index(
            "render_vehicle_management(",
        )
        ai_index = self.app_source.index(
            "# ---------- Garage AI ----------"
        )

        self.assertGreater(
            settings_index,
            twin_index,
        )
        self.assertLess(
            settings_index,
            ai_index,
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

    def test_long_workspaces_use_bounded_app_panes(self):
        self.assertIn(
            'key="vcg_twin_scroll"',
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

    def test_shell_styles_exist_for_primary_navigation_and_twin(self):
        self.assertIn(
            ".st-key-vcg_primary_nav",
            self.theme_source,
        )
        self.assertIn(
            ".vcg-twin-heading",
            self.theme_source,
        )
        self.assertIn(
            ".st-key-vcg_twin_scroll",
            self.theme_source,
        )


if __name__ == "__main__":
    unittest.main()
