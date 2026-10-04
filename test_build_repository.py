import unittest
from unittest.mock import MagicMock

from database import (
    add_vehicle_component,
    add_vehicle_component_event,
    update_vehicle_component,
)


class TestBuildRepository(unittest.TestCase):

    def test_add_vehicle_component_adds_owner_and_vehicle(self):
        client = MagicMock()
        response = MagicMock()
        response.data = [{"id": "component-1"}]

        (
            client.table.return_value
            .insert.return_value
            .select.return_value
            .execute.return_value
        ) = response

        component = {
            "name": "Coilovers",
            "component_type": "component",
        }

        result = add_vehicle_component(
            client,
            "user-1",
            2,
            component,
        )

        client.table.assert_called_once_with(
            "vehicle_components"
        )
        client.table.return_value.insert.assert_called_once_with(
            {
                "name": "Coilovers",
                "component_type": "component",
                "owner_id": "user-1",
                "vehicle_id": 2,
            }
        )
        self.assertNotIn(
            "owner_id",
            component,
        )
        self.assertEqual(
            result,
            response.data[0],
        )

    def test_update_vehicle_component_sets_updated_at(self):
        client = MagicMock()
        response = MagicMock()
        response.data = [{"id": "component-1"}]

        (
            client.table.return_value
            .update.return_value
            .eq.return_value
            .select.return_value
            .execute.return_value
        ) = response

        result = update_vehicle_component(
            client,
            "component-1",
            {
                "lifecycle_status": "planned",
            },
        )

        sent = (
            client.table.return_value
            .update.call_args.args[0]
        )

        self.assertEqual(
            sent["lifecycle_status"],
            "planned",
        )
        self.assertIn(
            "updated_at",
            sent,
        )
        self.assertEqual(
            result,
            response.data[0],
        )

    def test_add_component_event_records_catalogue_event(self):
        client = MagicMock()
        response = MagicMock()
        response.data = [{"id": "event-1"}]

        (
            client.table.return_value
            .insert.return_value
            .select.return_value
            .execute.return_value
        ) = response

        result = add_vehicle_component_event(
            client,
            "user-1",
            2,
            "component-1",
            "note",
            notes="Added to catalogue",
        )

        client.table.assert_called_once_with(
            "vehicle_component_events"
        )
        self.assertEqual(
            result,
            response.data[0],
        )


if __name__ == "__main__":
    unittest.main()
