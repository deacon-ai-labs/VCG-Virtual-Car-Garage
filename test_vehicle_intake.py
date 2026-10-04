import unittest

from vehicle_intake import (
    intake_snapshot,
    normalize_component_candidate,
    normalize_registration,
    normalize_vin,
)


class TestVehicleIntake(unittest.TestCase):

    def test_identity_values_are_normalized(self):
        self.assertEqual(
            normalize_registration(
                " ab12 cde "
            ),
            "AB12CDE",
        )
        self.assertEqual(
            normalize_vin(
                " shh-ep3-123 "
            ),
            "SHHEP3123",
        )

    def test_component_candidate_rejects_unknown_system(self):
        with self.assertRaises(
            ValueError
        ):
            normalize_component_candidate(
                {
                    "name": "Thing",
                    "system_key": "unknown_system",
                }
            )

    def test_ai_candidate_cannot_self_verify(self):
        candidate = normalize_component_candidate(
            {
                "name": "BC Racing Coilovers",
                "system_key": "suspension_steering",
                "confidence": "verified",
            }
        )

        self.assertEqual(
            candidate[
                "confidence"
            ],
            "medium",
        )

    def test_snapshot_blocks_completion_while_candidates_pending(self):
        snapshot = intake_snapshot(
            {
                "intake_status": "in_progress",
            },
            [],
            [
                {
                    "review_status": "pending",
                }
            ],
        )

        self.assertFalse(
            snapshot[
                "can_complete"
            ]
        )
        self.assertEqual(
            snapshot[
                "pending_count"
            ],
            1,
        )


if __name__ == "__main__":
    unittest.main()
