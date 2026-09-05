import unittest
from unittest.mock import MagicMock, patch

from database import (
    add_message,
    add_vehicle,
    create_conversation,
    delete_vehicle,
    get_conversations,
    get_messages,
    delete_conversation,
    rename_conversation,
    get_vehicle,
    get_vehicles,
    update_conversation_response_id,
    update_vehicle,
)


class TestDatabase(unittest.TestCase):

    def test_get_vehicles_uses_authenticated_client(self):
        client = MagicMock()

        response = MagicMock()
        response.data = [
            {
                "id": 1,
                "profile_name": "Deacon's EP3",
            }
        ]

        (
            client.table.return_value
            .select.return_value
            .order.return_value
            .execute.return_value
        ) = response

        result = get_vehicles(client)

        client.table.assert_called_once_with("vehicles")
        self.assertEqual(result, response.data)

    def test_get_vehicle_returns_visible_vehicle(self):
        client = MagicMock()

        response = MagicMock()
        response.data = [
            {
                "id": 1,
                "profile_name": "Deacon's EP3",
            }
        ]

        (
            client.table.return_value
            .select.return_value
            .eq.return_value
            .execute.return_value
        ) = response

        result = get_vehicle(client, 1)

        self.assertEqual(result, response.data[0])

    def test_add_vehicle_adds_owner_id(self):
        client = MagicMock()

        saved_vehicle = {
            "id": 3,
            "profile_name": "Test Car",
            "owner_id": "user-123",
        }

        response = MagicMock()
        response.data = [saved_vehicle]

        (
            client.table.return_value
            .insert.return_value
            .select.return_value
            .execute.return_value
        ) = response

        vehicle = {
            "profile_name": "Test Car",
            "manufacturer": "Honda",
            "model": "Civic",
            "year": 2004,
            "engine": "2.0",
            "mileage": 100000,
            "modifications": "",
        }

        result = add_vehicle(
            client,
            "user-123",
            vehicle,
        )

        client.table.return_value.insert.assert_called_once_with(
            {
                **vehicle,
                "owner_id": "user-123",
            }
        )

        self.assertNotIn("owner_id", vehicle)
        self.assertEqual(result, saved_vehicle)

    def test_update_vehicle_uses_authenticated_client(self):
        client = MagicMock()

        response = MagicMock()
        response.data = [
            {
                "id": 1,
                "profile_name": "Updated EP3",
            }
        ]

        (
            client.table.return_value
            .update.return_value
            .eq.return_value
            .select.return_value
            .execute.return_value
        ) = response

        changes = {
            "profile_name": "Updated EP3",
        }

        result = update_vehicle(
            client,
            1,
            changes,
        )

        client.table.return_value.update.assert_called_once_with(
            changes
        )

        self.assertEqual(result, response.data[0])

    def test_delete_vehicle_uses_authenticated_client(self):
        client = MagicMock()

        delete_query = (
            client.table.return_value
            .delete.return_value
        )

        delete_vehicle(client, 1)

        client.table.assert_called_once_with("vehicles")
        delete_query.eq.assert_called_once_with(
            "id",
            1,
        )

    def test_get_conversations_filters_by_vehicle_with_stable_order(self):
        client = MagicMock()

        response = MagicMock()
        response.data = [
            {
                "id": "conversation-1",
                "vehicle_id": 1,
                "title": "Tyre question",
            }
        ]

        (
            client.table.return_value
            .select.return_value
            .eq.return_value
            .order.return_value
            .execute.return_value
        ) = response

        result = get_conversations(
            client,
            1,
        )

        client.table.assert_called_once_with(
            "conversations"
        )

        (
            client.table.return_value
            .select.return_value
            .eq.assert_called_once_with(
                "vehicle_id",
                1,
            )
        )

        (
            client.table.return_value
            .select.return_value
            .eq.return_value
            .order.assert_called_once_with(
                "created_at",
                desc=True,
            )
        )

        self.assertEqual(
            result,
            response.data,
        )

    def test_create_conversation_adds_owner_and_vehicle(self):
        client = MagicMock()

        saved = {
            "id": "conversation-1",
            "owner_id": "user-123",
            "vehicle_id": 1,
            "title": "Tyre question",
        }

        response = MagicMock()
        response.data = [saved]

        (
            client.table.return_value
            .insert.return_value
            .select.return_value
            .execute.return_value
        ) = response

        result = create_conversation(
            client,
            "user-123",
            1,
            "Tyre question",
        )

        client.table.return_value.insert.assert_called_once_with(
            {
                "owner_id": "user-123",
                "vehicle_id": 1,
                "title": "Tyre question",
            }
        )

        self.assertEqual(
            result,
            saved,
        )

    def test_get_messages_orders_by_created_at(self):
        client = MagicMock()

        response = MagicMock()
        response.data = [
            {
                "role": "user",
                "content": "Hello",
            }
        ]

        (
            client.table.return_value
            .select.return_value
            .eq.return_value
            .order.return_value
            .execute.return_value
        ) = response

        result = get_messages(
            client,
            "conversation-1",
        )

        (
            client.table.return_value
            .select.return_value
            .eq.assert_called_once_with(
                "conversation_id",
                "conversation-1",
            )
        )

        (
            client.table.return_value
            .select.return_value
            .eq.return_value
            .order.assert_called_once_with(
                "created_at"
            )
        )

        self.assertEqual(
            result,
            response.data,
        )

    def test_add_message_saves_owner_role_and_content(self):
        client = MagicMock()

        saved = {
            "id": "message-1",
            "conversation_id": "conversation-1",
            "owner_id": "user-123",
            "role": "user",
            "content": "What tyres should I use?",
        }

        response = MagicMock()
        response.data = [saved]

        (
            client.table.return_value
            .insert.return_value
            .select.return_value
            .execute.return_value
        ) = response

        result = add_message(
            client,
            "user-123",
            "conversation-1",
            "user",
            "What tyres should I use?",
        )

        client.table.return_value.insert.assert_called_once_with(
            {
                "conversation_id": "conversation-1",
                "owner_id": "user-123",
                "role": "user",
                "content": "What tyres should I use?",
            }
        )

        self.assertEqual(
            result,
            saved,
        )

    @patch("database.datetime")
    def test_update_conversation_response_id(
        self,
        mock_datetime,
    ):
        client = MagicMock()

        mock_datetime.now.return_value.isoformat.return_value = (
            "2026-09-05T15:00:00+00:00"
        )

        update_conversation_response_id(
            client,
            "conversation-1",
            "resp_123",
        )

        client.table.assert_called_once_with(
            "conversations"
        )

        client.table.return_value.update.assert_called_once_with(
            {
                "last_response_id": "resp_123",
                "updated_at": "2026-09-05T15:00:00+00:00",
            }
        )

        (
            client.table.return_value
            .update.return_value
            .eq.assert_called_once_with(
                "id",
                "conversation-1",
            )
        )

    def test_rename_conversation_updates_title(self):
        client = MagicMock()

        response = MagicMock()
        response.data = [
            {
                "id": "conversation-1",
                "title": "EP3 tyre sizes",
            }
        ]

        (
            client.table.return_value
            .update.return_value
            .eq.return_value
            .select.return_value
            .execute.return_value
        ) = response

        result = rename_conversation(
            client,
            "conversation-1",
            "EP3 tyre sizes",
        )

        client.table.assert_called_once_with(
            "conversations"
        )

        client.table.return_value.update.assert_called_once_with(
            {
                "title": "EP3 tyre sizes",
            }
        )

        self.assertEqual(
            result,
            response.data[0],
        )

    def test_rename_conversation_rejects_blank_title(self):
        client = MagicMock()

        with self.assertRaises(ValueError):
            rename_conversation(
                client,
                "conversation-1",
                "   ",
            )

        client.table.assert_not_called()

    def test_delete_conversation_uses_authenticated_client(self):
        client = MagicMock()

        delete_query = (
            client.table.return_value
            .delete.return_value
        )

        delete_conversation(
            client,
            "conversation-1",
        )

        client.table.assert_called_once_with(
            "conversations"
        )

        delete_query.eq.assert_called_once_with(
            "id",
            "conversation-1",
        )


if __name__ == "__main__":
    unittest.main()
