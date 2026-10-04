import unittest
from pathlib import Path


class TestDiagnosticsUI(unittest.TestCase):

    def test_workspace_keeps_hypotheses_and_completed_checks_distinct(self):
        source = Path(
            "diagnostics_ui.py"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            '"Hypotheses"',
            source,
        )
        self.assertIn(
            '"Checks & evidence"',
            source,
        )
        self.assertIn(
            '"#### Completed evidence"',
            source,
        )
        self.assertIn(
            "A hypothesis is not a diagnosis",
            source,
        )

    def test_completed_check_requires_explicit_outcome_and_finding(self):
        source = Path(
            "diagnostics_ui.py"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "CHECK_OUTCOMES",
            source,
        )
        self.assertIn(
            '"status": "completed"',
            source,
        )
        self.assertIn(
            '"outcome": outcome',
            source,
        )
        self.assertIn(
            '"finding": finding.strip()',
            source,
        )


if __name__ == "__main__":
    unittest.main()
