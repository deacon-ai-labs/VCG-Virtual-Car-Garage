import unittest
from pathlib import Path


class TestM22VehicleIntakeIntegration(unittest.TestCase):

    def setUp(self):
        self.app = Path(
            "app.py"
        ).read_text(
            encoding="utf-8"
        )
        self.manage = Path(
            "vehicle_manage_ui.py"
        ).read_text(
            encoding="utf-8"
        )
        self.sql = Path(
            "supabase_m22_vehicle_intake.sql"
        ).read_text(
            encoding="utf-8"
        )

    def test_old_add_vehicle_form_is_replaced_by_intake(self):
        self.assertIn(
            "render_new_vehicle_intake_form(",
            self.app,
        )
        self.assertNotIn(
            '"add_vehicle_form"',
            self.app,
        )

    def test_twin_loads_evidence_and_review_candidates(self):
        self.assertIn(
            "get_vehicle_evidence(",
            self.app,
        )
        self.assertIn(
            "get_intake_candidates(",
            self.app,
        )
        self.assertIn(
            "render_vehicle_intake_panel(",
            self.app,
        )

    def test_vehicle_settings_preserve_registration_and_vin(self):
        self.assertIn(
            '"Registration"',
            self.manage,
        )
        self.assertIn(
            '"VIN"',
            self.manage,
        )
        self.assertIn(
            "normalize_registration(",
            self.manage,
        )
        self.assertIn(
            "normalize_vin(",
            self.manage,
        )

    def test_migration_keeps_evidence_private_and_approval_explicit(self):
        self.assertIn(
            "'vehicle-evidence'",
            self.sql,
        )
        self.assertIn(
            "public = excluded.public",
            self.sql,
        )
        self.assertIn(
            "approve_vehicle_intake_component_candidate",
            self.sql,
        )
        self.assertIn(
            "protect_approved_vehicle_evidence",
            self.sql,
        )
        self.assertIn(
            "complete_vehicle_intake",
            self.sql,
        )


if __name__ == "__main__":
    unittest.main()
