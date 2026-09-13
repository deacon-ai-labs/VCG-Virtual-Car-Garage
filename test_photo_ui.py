import unittest

from photo_ui import (
    build_photo_uploader_css,
    photo_upload_token,
)


class FakeUpload:
    def __init__(self, name, content_type, data):
        self.name = name
        self.type = content_type
        self._data = data

    def getvalue(self):
        return self._data


class TestPhotoUi(unittest.TestCase):

    def test_photo_upload_token_changes_with_content(self):
        first = FakeUpload(
            "car.jpg",
            "image/jpeg",
            b"abc",
        )
        second = FakeUpload(
            "car.jpg",
            "image/jpeg",
            b"abcd",
        )

        self.assertNotEqual(
            photo_upload_token(first),
            photo_upload_token(second),
        )

    def test_photo_uploader_css_uses_existing_photo_as_background(self):
        css = build_photo_uploader_css(
            "active_vehicle_photo_7",
            "https://example.test/car.jpg?token=abc",
        )

        self.assertIn(
            "background-image",
            css,
        )
        self.assertIn(
            "https://example.test/car.jpg?token=abc",
            css,
        )
        self.assertIn(
            "Click to change photo",
            css,
        )

    def test_photo_uploader_css_uses_add_copy_without_photo(self):
        css = build_photo_uploader_css(
            "active_vehicle_photo_7",
            None,
        )

        self.assertIn(
            "Click to add photo",
            css,
        )


if __name__ == "__main__":
    unittest.main()
