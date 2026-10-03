import unittest
from unittest.mock import patch

import verify_private_knowledge


class TestVerifyPrivateKnowledge(unittest.TestCase):

    @patch(
        "verify_private_knowledge.retrieve_knowledge"
    )
    def test_run_check_requires_vehicle_specific_evidence(
        self,
        mock_retrieve,
    ):
        mock_retrieve.return_value = [
            {
                "source_name": "Generic manual",
                "page_number": 1,
                "evidence_level": "generic_supplementary",
            }
        ]

        with self.assertRaises(
            RuntimeError
        ):
            verify_private_knowledge.run_check(
                {
                    "name": "test",
                    "question": "question",
                    "require_vehicle_specific": True,
                }
            )

    @patch(
        "verify_private_knowledge.retrieve_knowledge"
    )
    def test_run_check_accepts_vehicle_specific_evidence(
        self,
        mock_retrieve,
    ):
        mock_retrieve.return_value = [
            {
                "source_name": "Type R specification",
                "page_number": 1,
                "evidence_level": "vehicle_specific",
            }
        ]

        verify_private_knowledge.run_check(
            {
                "name": "test",
                "question": "question",
                "require_vehicle_specific": True,
            }
        )


if __name__ == "__main__":
    unittest.main()
