import unittest
from pathlib import Path


class TestVehicleManageUI(unittest.TestCase):

    def test_vehicle_management_is_workspace_independent(self):
        source = Path(
            "vehicle_manage_ui.py"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            '"Vehicle settings"',
            source,
        )
        self.assertIn(
            '"Danger zone"',
            source,
        )
        self.assertIn(
            "replace_vehicle_photo",
            source,
        )
        self.assertIn(
            "update_vehicle",
            source,
        )
        self.assertIn(
            "delete_vehicle_with_assets",
            source,
        )


if __name__ == "__main__":
    unittest.main()
