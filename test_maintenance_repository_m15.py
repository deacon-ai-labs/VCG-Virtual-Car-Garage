import unittest
from datetime import date
from unittest.mock import MagicMock

from database import (
    complete_maintenance_item,
    get_maintenance_records,
    record_maintenance_history,
)


class TestMaintenanceRepositoryM15(unittest.TestCase):

    def test_get_maintenance_records_orders_newest_first(self):
        client = MagicMock()
        response = MagicMock()
        response.data = [
            {
                "id": "record-1",
            }
        ]

        (
            client.table.return_value
            .select.return_value
            .eq.return_value
            .order.return_value
            .execute.return_value
        ) = response

        result = get_maintenance_records(
            client,
            2,
        )

        client.table.assert_called_once_with(
            "maintenance_records"
        )
        (
            client.table.return_value
            .select.return_value
            .eq.return_value
            .order.assert_called_once_with(
                "performed_at",
                desc=True,
            )
        )
        self.assertEqual(
            result,
            response.data,
        )

    def test_complete_maintenance_item_calls_atomic_rpc(self):
        client = MagicMock()
        response = MagicMock()
        response.data = {
            "maintenance_record_id": "record-1",
            "recurring": True,
        }

        client.rpc.return_value.execute.return_value = (
            response
        )

        result = complete_maintenance_item(
            client,
            "item-1",
            date(
                2026,
                10,
                4,
            ),
            performed_mileage=151500,
            cost_gbp=90.0,
            provider="Garage",
            notes="Oil and filter",
            evidence_reference="INV-1",
        )

        client.rpc.assert_called_once_with(
            "complete_maintenance_item",
            {
                "p_item_id": "item-1",
                "p_performed_at": "2026-10-04",
                "p_performed_mileage": 151500,
                "p_cost_gbp": 90.0,
                "p_provider": "Garage",
                "p_notes": "Oil and filter",
                "p_evidence_reference": "INV-1",
            },
        )
        self.assertEqual(
            result,
            response.data,
        )

    def test_record_history_calls_atomic_rpc(self):
        client = MagicMock()
        response = MagicMock()
        response.data = "record-1"

        client.rpc.return_value.execute.return_value = (
            response
        )

        result = record_maintenance_history(
            client,
            2,
            "Brake fluid",
            "fluid",
            date(
                2026,
                9,
                1,
            ),
            performed_mileage=150000,
            cost_gbp=60.0,
            provider="Garage",
            notes="Replaced",
            evidence_reference="Receipt",
            twin_component_id="component-1",
        )

        client.rpc.assert_called_once_with(
            "record_maintenance_history",
            {
                "p_vehicle_id": 2,
                "p_title": "Brake fluid",
                "p_category": "fluid",
                "p_performed_at": "2026-09-01",
                "p_performed_mileage": 150000,
                "p_cost_gbp": 60.0,
                "p_provider": "Garage",
                "p_notes": "Replaced",
                "p_evidence_reference": "Receipt",
                "p_twin_component_id": "component-1",
            },
        )

        self.assertEqual(
            result,
            "record-1",
        )


if __name__ == "__main__":
    unittest.main()
