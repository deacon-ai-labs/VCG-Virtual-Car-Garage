import unittest
from pathlib import Path


class TestFirstRunOnboarding(unittest.TestCase):

    def setUp(self):
        self.source = Path(
            "onboarding_ui.py"
        ).read_text(
            encoding="utf-8"
        )

    def test_first_run_is_vehicle_first(self):
        self.assertIn(
            "Your garage starts with one real car.",
            self.source,
        )
        self.assertIn(
            "Create your first Twin",
            self.source,
        )
        self.assertIn(
            "render_new_vehicle_intake_form(",
            self.source,
        )

    def test_first_run_does_not_force_public_sharing(self):
        self.assertNotIn(
            "render_public_garage_settings(",
            self.source,
        )
        self.assertNotIn(
            "Make my garage public",
            self.source,
        )


if __name__ == "__main__":
    unittest.main()
