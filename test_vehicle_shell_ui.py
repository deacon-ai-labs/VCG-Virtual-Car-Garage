import unittest
from pathlib import Path


class TestVehicleShellUI(unittest.TestCase):

    def test_command_deck_contains_core_vehicle_state(self):
        source = Path(
            "vehicle_shell_ui.py"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "MILEAGE",
            source,
        )
        self.assertIn(
            "MAINTENANCE",
            source,
        )
        self.assertIn(
            "DIAGNOSTICS",
            source,
        )
        self.assertIn(
            "BUILD",
            source,
        )
        self.assertIn(
            "vcg-command-deck",
            source,
        )


if __name__ == "__main__":
    unittest.main()
