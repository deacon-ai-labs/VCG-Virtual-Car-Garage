import unittest
from unittest.mock import MagicMock, patch

from public_garage_repository import (
    fetch_public_garage,
    sync_public_vehicle_photo,
)


class TestPublicGarageRepository(unittest.TestCase):

    def test_public_fetch_reads_only_published_snapshot(self):
        client = MagicMock()
        response = MagicMock()
        response.data = [
            {
                "payload": {
                    "slug": "deacons-garage",
                    "vehicles": [],
                }
            }
        ]

        (
            client.table.return_value
            .select.return_value
            .eq.return_value
            .limit.return_value
            .execute.return_value
        ) = response

        result = fetch_public_garage(
            client,
            "Deacons Garage",
        )

        client.table.assert_called_once_with(
            "public_garage_snapshots"
        )
        self.assertEqual(
            result[
                "slug"
            ],
            "deacons-garage",
        )

    def test_public_photo_path_is_opaque(self):
        source = __import__(
            "inspect"
        ).getsource(
            __import__(
                "public_garage_repository"
            ).publish_vehicle_photo_copy
        )

        self.assertIn(
            'f"{uuid4().hex}{suffix}"',
            source,
        )
        self.assertNotIn(
            'f"{owner_id}/"',
            source,
        )
        self.assertNotIn(
            'f"{vehicle[\'id\']}/"',
            source,
        )

    @patch(
        "public_garage_repository.publish_vehicle_photo_copy"
    )
    def test_photo_publish_requires_all_visibility_gates(
        self,
        publish_mock,
    ):
        client = MagicMock()
        profile = {
            "is_public": True,
            "show_photo": True,
            "public_photo_path": None,
        }
        vehicle = {
            "id": 2,
            "photo_path": "owner/2/photo.jpg",
        }

        sync_public_vehicle_photo(
            client=client,
            owner_id="owner",
            vehicle=vehicle,
            public_profile=profile,
            garage_is_public=False,
        )

        publish_mock.assert_not_called()

        sync_public_vehicle_photo(
            client=client,
            owner_id="owner",
            vehicle=vehicle,
            public_profile=profile,
            garage_is_public=True,
        )

        publish_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
