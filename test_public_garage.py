import unittest

from public_garage import (
    normalize_public_slug,
    public_slug_error,
    public_vehicle_defaults,
)


class TestPublicGarage(unittest.TestCase):

    def test_slug_is_normalized_for_share_link(self):
        self.assertEqual(
            normalize_public_slug(
                " Deacon's EP3 Garage "
            ),
            "deacons-ep3-garage",
        )

    def test_reserved_or_short_slug_is_rejected(self):
        self.assertIsNotNone(
            public_slug_error(
                "app"
            )
        )
        self.assertIsNotNone(
            public_slug_error(
                "a"
            )
        )
        self.assertIsNone(
            public_slug_error(
                "deacons-garage"
            )
        )

    def test_public_vehicle_defaults_are_privacy_first(self):
        profile = public_vehicle_defaults(
            2,
            "owner-1",
        )

        self.assertFalse(
            profile[
                "is_public"
            ]
        )
        self.assertFalse(
            profile[
                "show_engine"
            ]
        )
        self.assertFalse(
            profile[
                "show_mileage"
            ]
        )
        self.assertFalse(
            profile[
                "show_modifications"
            ]
        )
        self.assertFalse(
            profile[
                "show_specifications"
            ]
        )


if __name__ == "__main__":
    unittest.main()
