import unittest

from dashboard_state import apply_vehicle_selection


class TestDashboardState(unittest.TestCase):

    def test_same_vehicle_preserves_conversation(self):
        result = apply_vehicle_selection(
            current_vehicle_id=1,
            selected_vehicle_id=1,
            active_conversation_id="conversation-1",
        )

        self.assertEqual(
            result,
            {
                "active_vehicle_id": 1,
                "active_conversation_id": "conversation-1",
            },
        )

    def test_new_vehicle_starts_blank_chat(self):
        result = apply_vehicle_selection(
            current_vehicle_id=1,
            selected_vehicle_id=2,
            active_conversation_id="conversation-1",
        )

        self.assertEqual(
            result,
            {
                "active_vehicle_id": 2,
                "active_conversation_id": None,
            },
        )


if __name__ == "__main__":
    unittest.main()
