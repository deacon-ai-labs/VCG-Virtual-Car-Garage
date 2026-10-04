import unittest
from pathlib import Path


class TestVehicleIntakeUI(unittest.TestCase):

    def setUp(self):
        self.source = Path(
            "vehicle_intake_ui.py"
        ).read_text(
            encoding="utf-8"
        )

    def test_new_vehicle_intake_collects_identity_fields(self):
        self.assertIn(
            '"Registration"',
            self.source,
        )
        self.assertIn(
            '"VIN"',
            self.source,
        )
        self.assertIn(
            '"intake_status": "in_progress"',
            self.source,
        )

    def test_evidence_does_not_write_directly_to_twin(self):
        self.assertIn(
            "save_uploaded_evidence(",
            self.source,
        )
        self.assertIn(
            "Uploading evidence does not change the Twin by itself.",
            self.source,
        )

    def test_candidates_require_explicit_approval(self):
        self.assertIn(
            "Approve & add to Twin",
            self.source,
        )
        self.assertIn(
            "approve_component_candidate(",
            self.source,
        )
        self.assertIn(
            "reject_intake_candidate(",
            self.source,
        )

    def test_ai_extraction_preserves_source_text_and_creates_candidates(self):
        self.assertIn(
            "extract_modification_candidates(",
            self.source,
        )
        self.assertIn(
            "create_evidence_record(",
            self.source,
        )
        self.assertIn(
            '"source_kind": "manual_entry"',
            self.source,
        )
        self.assertIn(
            "create_intake_candidate(",
            self.source,
        )
        self.assertIn(
            'evidence_id=source_evidence[',
            self.source,
        )
        self.assertNotIn(
            "add_vehicle_component(",
            self.source,
        )


if __name__ == "__main__":
    unittest.main()
