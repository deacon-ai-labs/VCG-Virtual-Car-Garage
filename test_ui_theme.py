import unittest

from ui_theme import dashboard_shell_css


class TestDashboardShellCss(unittest.TestCase):

    def test_shell_leaves_room_for_chat_composer(self):
        css = dashboard_shell_css()

        self.assertIn(
            "calc(100vh - 360px)",
            css,
        )
        self.assertNotIn(
            ".block-container {\n            height: 100vh;\n            max-height: 100vh;\n            overflow: hidden;",
            css,
        )

    def test_chat_input_is_kept_above_scroll_area(self):
        css = dashboard_shell_css()

        self.assertIn(
            '[data-testid="stChatInput"]',
            css,
        )
        self.assertIn(
            "z-index: 4",
            css,
        )

    def test_mobile_css_restores_normal_page_scrolling(self):
        css = dashboard_shell_css()

        self.assertIn(
            "@media (max-width: 900px)",
            css,
        )
        self.assertIn(
            "[data-testid=\"stAppViewContainer\"]",
            css,
        )
        self.assertIn(
            "overflow-y: auto",
            css,
        )

    def test_mobile_css_removes_fixed_panel_heights(self):
        css = dashboard_shell_css()

        self.assertIn(
            ".st-key-vcg_garage_scroll",
            css,
        )
        self.assertIn(
            "height: auto",
            css,
        )
        self.assertIn(
            "max-height: none",
            css,
        )



if __name__ == "__main__":
    unittest.main()
