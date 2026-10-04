import unittest
from pathlib import Path


class TestStreamlitCompatibility(unittest.TestCase):

    def test_deprecated_container_width_api_is_not_used(self):
        app_source = Path(
            "app.py"
        ).read_text(
            encoding="utf-8"
        )

        self.assertNotIn(
            "use_container_width=",
            app_source,
        )


if __name__ == "__main__":
    unittest.main()
