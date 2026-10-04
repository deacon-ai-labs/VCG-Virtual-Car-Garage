import unittest
from unittest.mock import MagicMock

from vehicle_lifecycle import (
    delete_vehicle_with_assets,
    process_pending_storage_cleanup,
    queue_vehicle_asset_cleanup,
)


class TestVehicleLifecycle(unittest.TestCase):

    def test_cleanup_queue_deduplicates_asset_paths(self):
        client = MagicMock()

        queue_vehicle_asset_cleanup(
            client=client,
            owner_id="owner-1",
            vehicle={
                "id": 2,
                "photo_path": "owner-1/2/photo.jpg",
            },
            evidence=[
                {
                    "storage_path": "owner-1/2/invoice.pdf",
                },
                {
                    "storage_path": "owner-1/2/invoice.pdf",
                },
            ],
        )

        payload = (
            client.table.return_value
            .upsert.call_args.args[0]
        )

        self.assertEqual(
            len(
                payload
            ),
            2,
        )

    def test_delete_queues_assets_before_database_delete(self):
        client = MagicMock()

        process_response = MagicMock()
        process_response.data = []

        (
            client.table.return_value
            .select.return_value
            .eq.return_value
            .order.return_value
            .limit.return_value
            .execute.return_value
        ) = process_response

        delete_vehicle_with_assets(
            client=client,
            owner_id="owner-1",
            vehicle={
                "id": 2,
                "photo_path": "owner-1/2/photo.jpg",
            },
            evidence=[
                {
                    "storage_path": "owner-1/2/invoice.pdf",
                }
            ],
        )

        client.rpc.assert_called_once_with(
            "delete_vehicle_for_cleanup",
            {
                "p_vehicle_id": 2,
            },
        )

    def test_failed_storage_cleanup_stays_queued_for_retry(self):
        client = MagicMock()
        response = MagicMock()
        response.data = [
            {
                "id": "queue-1",
                "bucket_id": "vehicle-evidence",
                "storage_path": "owner-1/2/invoice.pdf",
                "attempts": 0,
            }
        ]

        (
            client.table.return_value
            .select.return_value
            .eq.return_value
            .order.return_value
            .limit.return_value
            .execute.return_value
        ) = response

        (
            client.storage.from_.return_value
            .remove.side_effect
        ) = RuntimeError(
            "temporary storage failure"
        )

        result = process_pending_storage_cleanup(
            client,
            "owner-1",
        )

        self.assertEqual(
            result[
                "failed"
            ],
            1,
        )

        update_payload = (
            client.table.return_value
            .update.call_args.args[0]
        )

        self.assertEqual(
            update_payload[
                "attempts"
            ],
            1,
        )
        self.assertEqual(
            update_payload[
                "last_error_type"
            ],
            "RuntimeError",
        )


if __name__ == "__main__":
    unittest.main()
