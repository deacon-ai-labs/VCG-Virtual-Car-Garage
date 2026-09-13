import unittest
from unittest.mock import MagicMock, patch

from photo_service import (
    remove_vehicle_photo,
    replace_vehicle_photo,
)


class TestPhotoService(unittest.TestCase):

    @patch("photo_service.delete_vehicle_photo")
    @patch("photo_service.update_vehicle_photo_path")
    @patch("photo_service.upload_vehicle_photo")
    def test_replace_vehicle_photo_updates_database_then_removes_old_photo(
        self,
        mock_upload,
        mock_update_path,
        mock_delete_photo,
    ):
        client = MagicMock()
        mock_upload.return_value = "user-1/7/new.jpg"

        result = replace_vehicle_photo(
            client=client,
            owner_id="user-1",
            vehicle_id=7,
            old_photo_path="user-1/7/old.jpg",
            filename="new.jpg",
            file_bytes=b"abc",
            content_type="image/jpeg",
        )

        mock_upload.assert_called_once()
        mock_update_path.assert_called_once_with(
            client,
            7,
            "user-1/7/new.jpg",
        )
        mock_delete_photo.assert_called_once_with(
            client,
            "user-1/7/old.jpg",
        )
        self.assertEqual(
            result,
            "user-1/7/new.jpg",
        )

    @patch("photo_service.delete_vehicle_photo")
    @patch("photo_service.update_vehicle_photo_path")
    @patch("photo_service.upload_vehicle_photo")
    def test_replace_vehicle_photo_cleans_up_new_upload_if_database_update_fails(
        self,
        mock_upload,
        mock_update_path,
        mock_delete_photo,
    ):
        client = MagicMock()
        mock_upload.return_value = "user-1/7/new.jpg"
        mock_update_path.side_effect = RuntimeError("db failed")

        with self.assertRaises(RuntimeError):
            replace_vehicle_photo(
                client=client,
                owner_id="user-1",
                vehicle_id=7,
                old_photo_path="user-1/7/old.jpg",
                filename="new.jpg",
                file_bytes=b"abc",
                content_type="image/jpeg",
            )

        mock_delete_photo.assert_called_once_with(
            client,
            "user-1/7/new.jpg",
        )

    @patch("photo_service.delete_vehicle_photo")
    @patch("photo_service.update_vehicle_photo_path")
    def test_remove_vehicle_photo_clears_database_then_deletes_object(
        self,
        mock_update_path,
        mock_delete_photo,
    ):
        client = MagicMock()

        remove_vehicle_photo(
            client=client,
            vehicle_id=7,
            photo_path="user-1/7/photo.jpg",
        )

        mock_update_path.assert_called_once_with(
            client,
            7,
            None,
        )
        mock_delete_photo.assert_called_once_with(
            client,
            "user-1/7/photo.jpg",
        )


if __name__ == "__main__":
    unittest.main()
