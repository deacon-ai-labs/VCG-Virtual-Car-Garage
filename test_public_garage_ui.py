import unittest
from pathlib import Path


class TestPublicGarageUI(unittest.TestCase):

    def setUp(self):
        self.source = Path(
            "public_garage_ui.py"
        ).read_text(
            encoding="utf-8"
        )

    def test_sharing_is_explicit_and_private_fields_are_named_as_excluded(self):
        self.assertIn(
            "Make my garage public",
            self.source,
        )
        self.assertIn(
            "Show this car publicly",
            self.source,
        )

        for private_term in (
            "VIN",
            "registration",
            "evidence",
            "diagnostics",
            "maintenance",
            "Garage AI",
        ):
            self.assertIn(
                private_term,
                self.source,
            )

    def test_public_page_uses_sanitised_payload_not_private_repositories(self):
        self.assertIn(
            "render_public_garage_showcase(",
            self.source,
        )
        self.assertIn(
            "public_photo_url(",
            self.source,
        )
        self.assertNotIn(
            "get_vehicle_evidence(",
            self.source,
        )
        self.assertNotIn(
            "get_diagnostic",
            self.source,
        )

    def test_owner_controls_cover_optional_vehicle_categories(self):
        for label in (
            '"Photo"',
            '"Year"',
            '"Manufacturer"',
            '"Model"',
            '"Engine"',
            '"Mileage"',
            '"Installed modifications"',
            '"Recorded specifications"',
        ):
            self.assertIn(
                label,
                self.source,
            )


if __name__ == "__main__":
    unittest.main()
