import unittest
from datetime import date

from maintenance_os import (
    maintenance_due_label,
    maintenance_health_snapshot,
    maintenance_is_due_soon,
    maintenance_is_overdue,
    maintenance_recurrence_label,
)


class TestMaintenanceOS(unittest.TestCase):

    def test_snapshot_prioritises_overdue_then_due_soon(self):
        items = [
            {
                "id": "overdue",
                "title": "Oil service",
                "status": "pending",
                "priority": "high",
                "due_mileage": 100000,
                "due_date": None,
                "sort_order": 0,
            },
            {
                "id": "soon",
                "title": "Brake inspection",
                "status": "pending",
                "priority": "normal",
                "due_mileage": 101500,
                "due_date": None,
                "sort_order": 1,
            },
        ]

        snapshot = maintenance_health_snapshot(
            items,
            [],
            current_mileage=100500,
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
            snapshot["due_soon_count"],
            1,
        )
        self.assertEqual(
            snapshot["next_actions"][0]["id"],
            "overdue",
        )

    def test_due_soon_uses_date_window_without_marking_overdue(self):
        item = {
            "status": "pending",
            "due_mileage": None,
            "due_date": "2026-10-20",
        }

        self.assertFalse(
            maintenance_is_overdue(
                item,
                0,
                today=date(
                    2026,
                    10,
                    4,
                ),
            )
        )
        self.assertTrue(
            maintenance_is_due_soon(
                item,
                0,
                today=date(
                    2026,
                    10,
                    4,
                ),
            )
        )

    def test_snapshot_sums_recorded_and_estimated_costs(self):
        snapshot = maintenance_health_snapshot(
            [
                {
                    "id": "1",
                    "status": "pending",
                    "estimated_cost_gbp": "120.50",
                    "due_mileage": None,
                    "due_date": None,
                }
            ],
            [
                {
                    "cost_gbp": "80.00",
                },
                {
                    "cost_gbp": None,
                },
            ],
            current_mileage=0,
        )

        self.assertEqual(
            snapshot["lifetime_cost_gbp"],
            80.0,
        )
        self.assertEqual(
            snapshot["estimated_open_cost_gbp"],
            120.5,
        )
        self.assertEqual(
            snapshot["history_count"],
            2,
        )

    def test_due_and_recurrence_labels_are_human_readable(self):
        item = {
            "due_mileage": 105000,
            "due_date": "2027-01-01",
            "interval_miles": 5000,
            "interval_months": 12,
        }

        self.assertEqual(
            maintenance_due_label(
                item
            ),
            "105,000 mi · 01 Jan 2027",
        )
        self.assertEqual(
            maintenance_recurrence_label(
                item
            ),
            "every 5,000 mi / every 12 months",
        )


if __name__ == "__main__":
    unittest.main()
