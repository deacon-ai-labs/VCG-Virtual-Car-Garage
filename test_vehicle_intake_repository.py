import unittest
from unittest.mock import MagicMock

from vehicle_intake_repository import (
    approve_component_candidate,
    save_uploaded_evidence,
)


class TestVehicleIntakeRepository(unittest.TestCase):

    def test_evidence_db_failure_removes_uploaded_object(self):
        client = MagicMock()

        upload_chain = (
            client.storage
            .from_.return_value
        )

        (
            client.table.return_value
            .insert.return_value
            .select.return_value
            .execute.side_effect
        ) = RuntimeError(
            "database failed"
        )

        with self.assertRaises(
            RuntimeError
        ):
            save_uploaded_evidence(
                client=client,
                owner_id="owner-1",
                vehicle_id=2,
                evidence_type="document",
                title="Invoice",
                filename="invoice.pdf",
                file_bytes=b"pdf",
                content_type="application/pdf",
            )

        upload_chain.remove.assert_called_once()

    def test_complete_intake_uses_guarded_rpc(self):
        client = MagicMock()
        response = MagicMock()
        response.data = {
            "id": 2,
            "intake_status": "complete",
        }

        (
            client.rpc.return_value
            .execute.return_value
        ) = response

        from vehicle_intake_repository import mark_intake_complete

        result = mark_intake_complete(
            client,
            2,
        )

        client.rpc.assert_called_once_with(
            "complete_vehicle_intake",
            {
                "p_vehicle_id": 2,
            },
        )
        self.assertEqual(
            result[
                "intake_status"
            ],
            "complete",
        )

    def test_approve_component_uses_transactional_rpc(self):
        client = MagicMock()
        response = MagicMock()
        response.data = "component-id"

        (
            client.rpc.return_value
            .execute.return_value
        ) = response

        result = approve_component_candidate(
            client,
            "candidate-id",
        )

        client.rpc.assert_called_once_with(
            "approve_vehicle_intake_component_candidate",
            {
                "p_candidate_id": "candidate-id",
            },
        )

        self.assertEqual(
            result,
            "component-id",
        )


if __name__ == "__main__":
    unittest.main()
