import unittest
from datetime import date

from dashboard_view import (
    maintenance_due_label,
    maintenance_snapshot,
    modification_items,
)


class TestDashboardView(unittest.TestCase):

    def test_modification_items_cleans_lines(self):
        self.assertEqual(
            modification_items(
                "- K100 remap\n"
                "• 4-2-1 manifold\n"
                "\n"
                "BC Racing coilovers"
            ),
            [
                "K100 remap",
                "4-2-1 manifold",
                "BC Racing coilovers",
            ],
        )

    def test_maintenance_snapshot_flags_due_mileage(self):
        snapshot = maintenance_snapshot(
            [
                {
                    "status": "pending",
                    "due_mileage": 90000,
                    "due_date": None,
                },
                {
                    "status": "completed",
                    "due_mileage": 80000,
                    "due_date": None,
                },
            ],
            current_mileage=95000,
            today=date(
                2026,
                10,
                4,
            ),
        )

        self.assertEqual(
            snapshot["state"],
            "Attention",
        )
        self.assertEqual(
            snapshot["overdue_count"],
            1,
        )
        self.assertEqual(
            snapshot["completed_count"],
            1,
        )

    def test_maintenance_snapshot_flags_due_date(self):
        snapshot = maintenance_snapshot(
            [
                {
                    "status": "pending",
                    "due_mileage": None,
                    "due_date": "2026-10-01",
                }
            ],
            current_mileage=0,
            today=date(
                2026,
                10,
                4,
            ),
        )

        self.assertEqual(
            snapshot["overdue_count"],
            1,
        )

    def test_due_label_combines_date_and_mileage(self):
        self.assertEqual(
            maintenance_due_label(
                {
                    "due_mileage": 100000,
                    "due_date": "2026-12-01",
                }
            ),
            "100,000 mi · 01 Dec 2026",
        )


if __name__ == "__main__":
    unittest.main()
