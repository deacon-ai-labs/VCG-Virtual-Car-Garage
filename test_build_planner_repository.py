import unittest
from datetime import date
from unittest.mock import MagicMock

from database import (
    cancel_build_plan_item,
    complete_build_plan_item,
    create_build_plan_install,
    create_build_plan_removal,
    get_build_plan_items,
    update_build_plan_item,
)


class TestBuildPlannerRepository(unittest.TestCase):

    def test_get_build_plan_items_filters_vehicle(self):
        client = MagicMock()
        response = MagicMock()
        response.data = [{"id": "plan-1"}]

        (
            client.table.return_value
            .select.return_value
            .eq.return_value
            .order.return_value
            .execute.return_value
        ) = response

        result = get_build_plan_items(
            client,
            2,
        )

        client.table.assert_called_once_with(
            "vehicle_build_plan_items"
        )
        self.assertEqual(
            result,
            response.data,
        )

    def test_create_install_uses_atomic_rpc(self):
        client = MagicMock()
        response = MagicMock()
        response.data = {
            "component_id": "component-1",
            "plan_item_id": "plan-1",
        }
        client.rpc.return_value.execute.return_value = response

        result = create_build_plan_install(
            client,
            2,
            "system-1",
            "Camshafts",
            manufacturer="Skunk2",
            estimated_cost_gbp=500.0,
        )

        self.assertEqual(
            client.rpc.call_args.args[0],
            "create_build_plan_install",
        )
        self.assertEqual(
            result,
            response.data,
        )

    def test_create_removal_uses_atomic_rpc(self):
        client = MagicMock()
        response = MagicMock()
        response.data = "plan-1"
        client.rpc.return_value.execute.return_value = response

        result = create_build_plan_removal(
            client,
            "component-1",
        )

        self.assertEqual(
            client.rpc.call_args.args[0],
            "create_build_plan_removal",
        )
        self.assertEqual(
            result,
            "plan-1",
        )

    def test_update_plan_limits_editable_fields(self):
        client = MagicMock()
        response = MagicMock()
        response.data = [{"id": "plan-1"}]

        (
            client.table.return_value
            .update.return_value
            .eq.return_value
            .select.return_value
            .execute.return_value
        ) = response

        update_build_plan_item(
            client,
            "plan-1",
            {
                "status": "ready",
                "priority": "high",
                "action": "remove",
            },
        )

        changes = (
            client.table.return_value
            .update.call_args.args[0]
        )

        self.assertEqual(
            changes["status"],
            "ready",
        )
        self.assertEqual(
            changes["priority"],
            "high",
        )
        self.assertNotIn(
            "action",
            changes,
        )

    def test_complete_plan_calls_rpc(self):
        client = MagicMock()
        response = MagicMock()
        response.data = {"status": "completed"}
        client.rpc.return_value.execute.return_value = response

        result = complete_build_plan_item(
            client,
            "plan-1",
            date(
                2026,
                10,
                4,
            ),
            mileage=151500,
            actual_cost_gbp=500.0,
            notes="Installed",
        )

        client.rpc.assert_called_once_with(
            "complete_build_plan_item",
            {
                "p_plan_item_id": "plan-1",
                "p_completed_at": "2026-10-04",
                "p_mileage": 151500,
                "p_actual_cost_gbp": 500.0,
                "p_notes": "Installed",
            },
        )
        self.assertEqual(
            result,
            response.data,
        )

    def test_cancel_plan_calls_rpc(self):
        client = MagicMock()
        response = MagicMock()
        response.data = {"status": "cancelled"}
        client.rpc.return_value.execute.return_value = response

        result = cancel_build_plan_item(
            client,
            "plan-1",
            notes="Changed mind",
        )

        client.rpc.assert_called_once_with(
            "cancel_build_plan_item",
            {
                "p_plan_item_id": "plan-1",
                "p_notes": "Changed mind",
            },
        )
        self.assertEqual(
            result,
            response.data,
        )


if __name__ == "__main__":
    unittest.main()
