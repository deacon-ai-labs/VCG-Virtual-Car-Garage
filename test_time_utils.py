import unittest

from time_utils import format_local_timestamp


class TestTimeUtils(unittest.TestCase):

    def test_formats_utc_as_london_bst(self):
        result = format_local_timestamp(
            "2026-09-13T12:00:00+00:00",
            "Europe/London",
        )

        self.assertEqual(
            result,
            "13 Sep 13:00",
        )

    def test_formats_utc_as_new_york_local_time(self):
        result = format_local_timestamp(
            "2026-09-13T12:00:00+00:00",
            "America/New_York",
        )

        self.assertEqual(
            result,
            "13 Sep 08:00",
        )

    def test_naive_timestamp_is_treated_as_utc(self):
        result = format_local_timestamp(
            "2026-09-13T12:00:00",
            "Europe/London",
        )

        self.assertEqual(
            result,
            "13 Sep 13:00",
        )

    def test_invalid_timezone_falls_back_to_utc(self):
        result = format_local_timestamp(
            "2026-09-13T12:00:00+00:00",
            "Not/A_Timezone",
        )

        self.assertEqual(
            result,
            "13 Sep 12:00",
        )


if __name__ == "__main__":
    unittest.main()
