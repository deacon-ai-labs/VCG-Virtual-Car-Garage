import unittest
from unittest.mock import MagicMock, patch

import auth


class TestAuth(unittest.TestCase):

    @patch("auth.get_supabase_client")
    def test_sign_up_uses_email_and_password(
        self,
        mock_get_supabase_client,
    ):
        client = MagicMock()
        mock_get_supabase_client.return_value = client

        auth.sign_up(
            "deacon@example.com",
            "example-password",
        )

        client.auth.sign_up.assert_called_once_with(
            {
                "email": "deacon@example.com",
                "password": "example-password",
            }
        )

    @patch("auth.get_supabase_client")
    def test_sign_in_uses_email_and_password(
        self,
        mock_get_supabase_client,
    ):
        client = MagicMock()
        mock_get_supabase_client.return_value = client

        auth.sign_in(
            "deacon@example.com",
            "example-password",
        )

        client.auth.sign_in_with_password.assert_called_once_with(
            {
                "email": "deacon@example.com",
                "password": "example-password",
            }
        )

    @patch("auth.get_supabase_client")
    def test_create_authenticated_client_restores_session(
        self,
        mock_get_supabase_client,
    ):
        client = MagicMock()
        mock_get_supabase_client.return_value = client

        result = auth.create_authenticated_client(
            "access-token",
            "refresh-token",
        )

        client.auth.set_session.assert_called_once_with(
            "access-token",
            "refresh-token",
        )

        self.assertIs(result, client)

    def test_sign_out_calls_supabase_sign_out(self):
        client = MagicMock()

        auth.sign_out(client)

        client.auth.sign_out.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
