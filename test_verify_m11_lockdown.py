import unittest
from unittest.mock import MagicMock, patch

import verify_m11_lockdown


class TestM11LockdownVerifier(unittest.TestCase):

    @patch(
        "verify_m11_lockdown.get_supabase_client"
    )
    def test_public_table_access_is_failure_if_query_succeeds(
        self,
        mock_get_client,
    ):
        client = MagicMock()
        mock_get_client.return_value = client

        with self.assertRaises(RuntimeError):
            verify_m11_lockdown.expect_public_table_blocked()

    @patch(
        "verify_m11_lockdown.get_supabase_client"
    )
    def test_public_table_access_passes_when_query_is_rejected(
        self,
        mock_get_client,
    ):
        client = MagicMock()
        mock_get_client.return_value = client

        (
            client.table.return_value
            .select.return_value
            .limit.return_value
            .execute.side_effect
        ) = Exception(
            "permission denied"
        )

        verify_m11_lockdown.expect_public_table_blocked()

    @patch(
        "verify_m11_lockdown.retrieve_knowledge"
    )
    def test_server_rag_requires_vehicle_specific_evidence(
        self,
        mock_retrieve,
    ):
        mock_retrieve.return_value = [
            {
                "evidence_level": (
                    "generic_supplementary"
                )
            }
        ]

        with self.assertRaises(RuntimeError):
            verify_m11_lockdown.expect_server_rag_works()


if __name__ == "__main__":
    unittest.main()
