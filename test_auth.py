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
                "options": {
                    "email_redirect_to": (
                        "https://virtual-car-garage.streamlit.app/"
                    ),
                },
            }
        )

    @patch("auth.get_supabase_client")
    def test_sign_up_can_override_confirmation_redirect(
        self,
        mock_get_supabase_client,
    ):
        client = MagicMock()
        mock_get_supabase_client.return_value = client

        auth.sign_up(
            "deacon@example.com",
            "example-password",
            redirect_url="https://example.com/",
        )

        client.auth.sign_up.assert_called_once_with(
            {
                "email": "deacon@example.com",
                "password": "example-password",
                "options": {
                    "email_redirect_to": "https://example.com/",
                },
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

    def test_auth_error_message_identifies_api_key_problem(self):
        message = auth.user_auth_error_message(
            Exception(
                "UNAUTHORIZED_UNREGISTERED_API_KEY: Unregistered API key"
            )
        )

        self.assertIn(
            "misconfigured",
            message,
        )
        self.assertNotIn(
            "email and password",
            message,
        )

    def test_auth_error_message_identifies_email_rate_limit(self):
        message = auth.user_auth_error_message(
            Exception(
                "429: email rate limit exceeded "
                "(over_email_send_rate_limit)"
            ),
            action="create the account",
        )

        self.assertIn(
            "temporarily rate-limited",
            message,
        )
        self.assertIn(
            "try again",
            message,
        )
        self.assertNotIn(
            "unexpected error",
            message,
        )

    def test_auth_error_message_keeps_bad_credentials_user_friendly(self):
        message = auth.user_auth_error_message(
            Exception(
                "Invalid login credentials"
            )
        )

        self.assertIn(
            "email and password",
            message,
        )

    def test_signup_password_policy_rejects_short_or_simple_passwords(self):
        self.assertIsNotNone(
            auth.signup_password_error(
                "short1"
            )
        )
        self.assertIsNotNone(
            auth.signup_password_error(
                "abcdefghijklmnop"
            )
        )
        self.assertIsNone(
            auth.signup_password_error(
                "very-long-password-123"
            )
        )

    def test_sign_out_calls_supabase_sign_out(self):
        client = MagicMock()

        auth.sign_out(client)

        client.auth.sign_out.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
