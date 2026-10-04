import unittest
from unittest.mock import MagicMock, patch

from garage_ai import ask_ai


class TestGarageAIM16(unittest.TestCase):

    def test_instructions_keep_planned_build_separate_from_physical_state(self):
        response = MagicMock()
        response.output_text = "Answer"

        with (
            patch(
                "garage_ai.client.responses.create",
                return_value=response,
            ) as create_mock,
            patch(
                "garage_ai.get_reference_context",
                return_value="REFERENCE",
            ),
        ):
            ask_ai(
                user_message="Are the planned cams fitted?",
                vehicle_description=(
                    "Current physical structured build (source of truth):\n"
                    "- K100 ECU\n"
                    "Active future build plan "
                    "(NOT physically fitted/removed yet):\n"
                    "- Camshafts; action=install; plan_status=planned"
                ),
                previous_response_id=None,
            )

        instructions = create_mock.call_args.kwargs[
            "instructions"
        ]

        self.assertIn(
            "hypothetical future intent",
            instructions,
        )
        self.assertIn(
            "Never describe a planned installation as fitted",
            instructions,
        )
        self.assertIn(
            "planning metadata, not technical proof",
            instructions,
        )


if __name__ == "__main__":
    unittest.main()
