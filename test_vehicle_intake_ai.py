import json
import unittest
from unittest.mock import MagicMock, patch

from vehicle_intake_ai import extract_modification_candidates


class TestVehicleIntakeAI(unittest.TestCase):

    def test_extractor_keeps_unknown_values_unknown(self):
        response = MagicMock()
        response.output_text = json.dumps(
            {
                "components": [
                    {
                        "name": "4-2-1 Exhaust Manifold",
                        "system_key": "exhaust",
                        "manufacturer": None,
                        "part_number": None,
                        "position": None,
                        "notes": None,
                        "is_oem": False,
                        "confidence": "medium",
                    }
                ]
            }
        )

        with patch(
            "vehicle_intake_ai.client.responses.create",
            return_value=response,
        ) as create_mock:
            result = extract_modification_candidates(
                "It has a 4-2-1 manifold fitted.",
                "2004 Honda Civic Type R EP3",
            )

        self.assertEqual(
            result[0][
                "manufacturer"
            ],
            None,
        )
        self.assertEqual(
            result[0][
                "system_key"
            ],
            "exhaust",
        )

        instructions = create_mock.call_args.kwargs[
            "instructions"
        ]

        self.assertIn(
            "Never invent",
            instructions,
        )
        self.assertIn(
            "future plans or wishes",
            instructions,
        )

    def test_empty_text_skips_model_call(self):
        with patch(
            "vehicle_intake_ai.client.responses.create"
        ) as create_mock:
            result = extract_modification_candidates(
                "   ",
                "Car",
            )

        self.assertEqual(
            result,
            [],
        )
        create_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
