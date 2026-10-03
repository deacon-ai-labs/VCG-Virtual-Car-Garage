import os
import unittest
from unittest.mock import patch

from knowledge_admin import (
    get_knowledge_admin_client,
    get_private_knowledge_credentials,
)


class TestKnowledgeAdmin(unittest.TestCase):

    @patch.dict(
        os.environ,
        {},
        clear=True,
    )
    def test_admin_client_requires_private_credentials(self):
        with self.assertRaises(RuntimeError):
            get_knowledge_admin_client()

    @patch.dict(
        os.environ,
        {
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_SECRET_KEY": "Value:\nbad-secret",
        },
        clear=True,
    )
    def test_rejects_labelled_multiline_secret_without_echoing_it(self):
        with self.assertRaises(RuntimeError) as context:
            get_private_knowledge_credentials()

        message = str(context.exception)

        self.assertIn(
            "SUPABASE_SECRET_KEY is malformed",
            message,
        )
        self.assertNotIn(
            "bad-secret",
            message,
        )

    @patch.dict(
        os.environ,
        {
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_SECRET_KEY": "sb_secret_test_key",
        },
        clear=True,
    )
    def test_returns_clean_private_credentials(self):
        url, key = get_private_knowledge_credentials()

        self.assertEqual(
            url,
            "https://example.supabase.co",
        )
        self.assertEqual(
            key,
            "sb_secret_test_key",
        )


if __name__ == "__main__":
    unittest.main()
