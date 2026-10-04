import unittest
from datetime import date
from unittest.mock import patch

from virtual_workshop import (
    system_status_label,
    workshop_blueprint_html,
    workshop_snapshot,
)


class TestVirtualWorkshop(unittest.TestCase):

    def setUp(self):
        self.components = [
            {
                "id": "root-engine",
                "component_type": "system",
                "parent_component_id": None,
                "system_key": "engine",
                "name": "Engine",
                "lifecycle_status": "installed",
            },
            {
                "id": "engine-current",
                "component_type": "component",
                "parent_component_id": "root-engine",
                "system_key": "engine",
                "name": "K100 ECU",
                "lifecycle_status": "installed",
                "weight_kg": 1.2,
                "quantity": 1,
            },
            {
                "id": "engine-plan",
                "component_type": "component",
                "parent_component_id": "root-engine",
                "system_key": "engine",
                "name": "Camshafts",
                "lifecycle_status": "planned",
                "weight_kg": 4,
                "quantity": 1,
            },
            {
                "id": "root-brakes",
                "component_type": "system",
                "parent_component_id": None,
                "system_key": "brakes",
                "name": "Brakes",
                "lifecycle_status": "installed",
            },
        ]

    @patch(
        "virtual_workshop.maintenance_is_due_soon",
        return_value=False,
    )
    @patch(
        "virtual_workshop.maintenance_is_overdue",
        return_value=False,
    )
    def test_snapshot_groups_twin_and_plan_by_system(
        self,
        _overdue,
        _due_soon,
    ):
        snapshot = workshop_snapshot(
            self.components,
            [
                {
                    "component_id": "engine-plan",
                    "action": "install",
                    "status": "planned",
                }
            ],
            [],
            [],
            [],
            current_mileage=151500,
        )

        engine = snapshot[
            "system_lookup"
        ][
            "engine"
        ]

        self.assertEqual(
            engine[
                "installed_count"
            ],
            1,
        )
        self.assertEqual(
            engine[
                "planned_count"
            ],
            1,
        )
        self.assertEqual(
            engine[
                "state"
            ],
            "planned",
        )
        self.assertEqual(
            snapshot[
                "active_plan_count"
            ],
            1,
        )

    @patch(
        "virtual_workshop.maintenance_is_due_soon",
        return_value=False,
    )
    @patch(
        "virtual_workshop.maintenance_is_overdue",
        return_value=True,
    )
    def test_overdue_maintenance_takes_visual_priority(
        self,
        _overdue,
        _due_soon,
    ):
        snapshot = workshop_snapshot(
            self.components,
            [],
            [
                {
                    "id": "maint-1",
                    "status": "pending",
                    "twin_component_id": "root-brakes",
                }
            ],
            [],
            [],
            current_mileage=151500,
        )

        brakes = snapshot[
            "system_lookup"
        ][
            "brakes"
        ]

        self.assertEqual(
            brakes[
                "state"
            ],
            "attention",
        )
        self.assertEqual(
            system_status_label(
                brakes
            ),
            "Maintenance attention",
        )

    @patch(
        "virtual_workshop.maintenance_is_due_soon",
        return_value=False,
    )
    @patch(
        "virtual_workshop.maintenance_is_overdue",
        return_value=False,
    )
    def test_blueprint_contains_system_activity_counts(
        self,
        _overdue,
        _due_soon,
    ):
        snapshot = workshop_snapshot(
            self.components,
            [
                {
                    "component_id": "engine-plan",
                    "action": "install",
                    "status": "planned",
                }
            ],
            [],
            [],
            [],
            current_mileage=151500,
        )

        html = workshop_blueprint_html(
            snapshot,
            "engine",
        )

        self.assertIn(
            "Engine",
            html,
        )
        self.assertIn(
            "1 fitted · 1 planned",
            html,
        )
        self.assertIn(
            "Vehicle digital twin workshop schematic",
            html,
        )


if __name__ == "__main__":
    unittest.main()
