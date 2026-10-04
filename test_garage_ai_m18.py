import unittest
from unittest.mock import MagicMock, patch

from garage_ai import ask_ai


class TestGarageAIM18(unittest.TestCase):

    def test_vehicle_intelligence_is_injected_with_authority_rules(self):
        response = MagicMock()
        response.output_text = "Answer"

        intelligence = (
            "CURRENT PHYSICAL BUILD — RECORDED DIGITAL-TWIN STATE:\n"
            "- BC Racing Coilovers; system=suspension_steering\n\n"
            "OPEN MAINTENANCE — RECORDED SCHEDULE/ADVISORY STATE:\n"
            "- Front brake inspection; state=overdue\n\n"
            "SERVICE HISTORY — USER/APP-RECORDED PAST WORK:\n"
            "- Brake fluid; performed_at=2026-09-01"
        )

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
                user_message="Why might the car pull left?",
                vehicle_description=(
                    "2004 Honda Civic Type R EP3; engine=K20A2"
                ),
                vehicle_intelligence_context=(
                    intelligence
                ),
                previous_response_id=None,
            )

        instructions = create_mock.call_args.kwargs[
            "instructions"
        ]

        self.assertIn(
            intelligence,
            instructions,
        )
        self.assertIn(
            "recorded vehicle state",
            instructions,
        )
        self.assertIn(
            "They do not prove the component is currently healthy",
            instructions,
        )
        self.assertIn(
            "Never turn correlation in the vehicle history into causation",
            instructions,
        )
        self.assertIn(
            "Prefer checks that discriminate between likely causes",
            instructions,
        )

    def test_plan_metadata_is_not_promoted_to_technical_proof(self):
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
                user_message="Will these cams definitely fit?",
                vehicle_description=(
                    "2004 Honda Civic Type R EP3"
                ),
                vehicle_intelligence_context=(
                    "ACTIVE FUTURE BUILD PLAN — INTENT ONLY, NOT PHYSICAL STATE:\n"
                    "- Camshafts; compatibility_status=compatible"
                ),
                previous_response_id=None,
            )

        instructions = create_mock.call_args.kwargs[
            "instructions"
        ]

        self.assertIn(
            "planning metadata, not technical proof",
            instructions,
        )
        self.assertIn(
            "ACTIVE FUTURE BUILD PLAN is intent only",
            instructions,
        )


if __name__ == "__main__":
    unittest.main()
