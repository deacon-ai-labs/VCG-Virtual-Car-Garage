import unittest
from pathlib import Path


class TestVirtualTwinV0UI(unittest.TestCase):

    def test_twin_exposes_contextual_actions_not_dashboard_tabs(self):
        source = Path(
            "virtual_twin_v0_ui.py"
        ).read_text(
            encoding="utf-8"
        )

        for label in (
            "Inspect",
            "Maintain",
            "Diagnose",
            "Modify",
            "AI",
        ):
            self.assertIn(
                f'"{label}"',
                source,
            )

        self.assertIn(
            "OWNED TWIN",
            source,
        )
        self.assertNotIn(
            "st.tabs(",
            source,
        )

    def test_twin_does_not_invent_performance_numbers(self):
        source = Path(
            "virtual_twin_v0_ui.py"
        ).read_text(
            encoding="utf-8"
        )

        self.assertNotIn(
            "WHP",
            source,
        )
        self.assertNotIn(
            "PI Index",
            source,
        )


if __name__ == "__main__":
    unittest.main()
