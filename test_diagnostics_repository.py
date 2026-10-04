import unittest
from unittest.mock import MagicMock

from database import (
    add_diagnostic_case,
    get_diagnostic_cases,
    update_diagnostic_check,
)


class TestDiagnosticsRepository(unittest.TestCase):

    def test_get_cases_filters_vehicle_and_orders_activity(self):
        client = MagicMock()
        response = MagicMock()
        response.data = [
            {
                "id": "case-1",
            }
        ]

        (
            client.table.return_value
            .select.return_value
            .eq.return_value
            .order.return_value
            .execute.return_value
        ) = response

        result = get_diagnostic_cases(
            client,
            2,
        )

        client.table.assert_called_once_with(
            "diagnostic_cases"
        )

        (
            client.table.return_value
            .select.return_value
            .eq.assert_called_once_with(
                "vehicle_id",
                2,
            )
        )

        (
            client.table.return_value
            .select.return_value
            .eq.return_value
            .order.assert_called_once_with(
                "updated_at",
                desc=True,
            )
        )

        self.assertEqual(
            result,
            response.data,
        )

    def test_add_case_injects_owner_and_vehicle(self):
        client = MagicMock()
        response = MagicMock()
        response.data = [
            {
                "id": "case-1",
            }
        ]

        (
            client.table.return_value
            .insert.return_value
            .select.return_value
            .execute.return_value
        ) = response

        result = add_diagnostic_case(
            client,
            "owner-1",
            2,
            {
                "title": "Pull left",
                "symptom_description": "Pulls under braking",
            },
        )

        payload = (
            client.table.return_value
            .insert.call_args.args[0]
        )

        self.assertEqual(
            payload[
                "owner_id"
            ],
            "owner-1",
        )
        self.assertEqual(
            payload[
                "vehicle_id"
            ],
            2,
        )
        self.assertEqual(
            result,
            response.data[0],
        )

    def test_update_check_rejects_unknown_fields(self):
        client = MagicMock()
        response = MagicMock()
        response.data = [
            {
                "id": "check-1",
            }
        ]

        (
            client.table.return_value
            .update.return_value
            .eq.return_value
            .select.return_value
            .execute.return_value
        ) = response

        update_diagnostic_check(
            client,
            "check-1",
            {
                "status": "completed",
                "outcome": "supports",
                "finding": "Right side hotter",
                "owner_id": "should-not-change",
                "vehicle_id": 99,
            },
        )

        payload = (
            client.table.return_value
            .update.call_args.args[0]
        )

        self.assertEqual(
            payload[
                "status"
            ],
            "completed",
        )
        self.assertEqual(
            payload[
                "outcome"
            ],
            "supports",
        )
        self.assertNotIn(
            "owner_id",
            payload,
        )
        self.assertNotIn(
            "vehicle_id",
            payload,
        )


if __name__ == "__main__":
    unittest.main()
