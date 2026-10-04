import unittest

from upload_security import (
    MAX_EVIDENCE_BYTES,
    validate_evidence_upload,
    validate_vehicle_photo_upload,
)


class TestUploadSecurity(unittest.TestCase):

    def test_valid_jpeg_signature_is_accepted(self):
        validate_vehicle_photo_upload(
            b"\xff\xd8\xff\xe0",
            "image/jpeg",
        )

    def test_spoofed_jpeg_is_rejected(self):
        with self.assertRaises(
            ValueError
        ):
            validate_vehicle_photo_upload(
                b"not-an-image",
                "image/jpeg",
            )

    def test_valid_pdf_signature_is_accepted(self):
        validate_evidence_upload(
            b"%PDF-1.7\nminimal",
            "application/pdf",
        )

    def test_spoofed_pdf_is_rejected(self):
        with self.assertRaises(
            ValueError
        ):
            validate_evidence_upload(
                b"plain text pretending to be pdf",
                "application/pdf",
            )

    def test_invalid_json_is_rejected(self):
        with self.assertRaises(
            ValueError
        ):
            validate_evidence_upload(
                b"{not-json}",
                "application/json",
            )

    def test_oversized_evidence_is_rejected_before_storage(self):
        with self.assertRaises(
            ValueError
        ):
            validate_evidence_upload(
                b"a" * (
                    MAX_EVIDENCE_BYTES
                    + 1
                ),
                "text/plain",
            )


if __name__ == "__main__":
    unittest.main()
