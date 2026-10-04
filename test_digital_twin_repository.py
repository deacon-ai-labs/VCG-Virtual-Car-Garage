import unittest
from unittest.mock import MagicMock

from database import (
    get_vehicle_component_events,
    get_vehicle_components,
    get_vehicle_specifications,
)


class TestDigitalTwinRepository(unittest.TestCase):

    def test_get_vehicle_components_filters_vehicle(self):
        client = MagicMock()
        response = MagicMock()
        response.data = [{"id": "component-1"}]

        (
            client.table.return_value
            .select.return_value
            .eq.return_value
            .order.return_value
            .execute.return_value
        ) = response

        result = get_vehicle_components(
            client,
            2,
        )

        client.table.assert_called_once_with(
            "vehicle_components"
        )
        (
            client.table.return_value
            .select.return_value
            .eq.assert_called_once_with(
                "vehicle_id",
                2,
            )
        )
        self.assertEqual(
            result,
            response.data,
        )

    def test_get_vehicle_specifications_returns_current_specs(self):
        client = MagicMock()
        response = MagicMock()
        response.data = [{"id": "spec-1"}]

        (
            client.table.return_value
            .select.return_value
            .eq.return_value
            .eq.return_value
            .order.return_value
            .execute.return_value
        ) = response

        result = get_vehicle_specifications(
            client,
            2,
        )

        client.table.assert_called_once_with(
            "vehicle_specifications"
        )
        self.assertEqual(
            result,
            response.data,
        )

    def test_get_vehicle_component_events_orders_newest_first(self):
        client = MagicMock()
        response = MagicMock()
        response.data = [{"id": "event-1"}]

        (
            client.table.return_value
            .select.return_value
            .eq.return_value
            .order.return_value
            .execute.return_value
        ) = response

        result = get_vehicle_component_events(
            client,
            2,
        )

        (
            client.table.return_value
            .select.return_value
            .eq.return_value
            .order.assert_called_once_with(
                "occurred_at",
                desc=True,
            )
        )
        self.assertEqual(
            result,
            response.data,
        )


if __name__ == "__main__":
    unittest.main()
