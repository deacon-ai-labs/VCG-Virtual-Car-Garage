from __future__ import annotations

import json


MAX_EVIDENCE_BYTES = 15 * 1024 * 1024
MAX_VEHICLE_PHOTO_BYTES = 8 * 1024 * 1024


def _is_jpeg(
    data: bytes,
) -> bool:
    return (
        len(
            data
        )
        >= 4
        and data[:3]
        == b"\xff\xd8\xff"
    )


def _is_png(
    data: bytes,
) -> bool:
    return data.startswith(
        b"\x89PNG\r\n\x1a\n"
    )


def _is_webp(
    data: bytes,
) -> bool:
    return (
        len(
            data
        )
        >= 12
        and data[:4]
        == b"RIFF"
        and data[8:12]
        == b"WEBP"
    )


def _validate_image_signature(
    data: bytes,
    content_type: str,
) -> None:
    validators = {
        "image/jpeg": _is_jpeg,
        "image/png": _is_png,
        "image/webp": _is_webp,
    }

    validator = validators.get(
        content_type
    )

    if (
        validator is None
        or not validator(
            data
        )
    ):
        raise ValueError(
            "The uploaded image content does not match its declared file type."
        )


def validate_vehicle_photo_upload(
    file_bytes: bytes,
    content_type: str,
) -> None:
    if not file_bytes:
        raise ValueError(
            "Vehicle photo cannot be empty."
        )

    if len(
        file_bytes
    ) > MAX_VEHICLE_PHOTO_BYTES:
        raise ValueError(
            "Vehicle photo must be 8 MB or smaller."
        )

    _validate_image_signature(
        file_bytes,
        content_type,
    )


def validate_evidence_upload(
    file_bytes: bytes,
    content_type: str,
) -> None:
    if not file_bytes:
        raise ValueError(
            "Evidence file cannot be empty."
        )

    if len(
        file_bytes
    ) > MAX_EVIDENCE_BYTES:
        raise ValueError(
            "Evidence file must be 15 MB or smaller."
        )

    if content_type.startswith(
        "image/"
    ):
        _validate_image_signature(
            file_bytes,
            content_type,
        )
        return

    if content_type == "application/pdf":
        if not file_bytes.startswith(
            b"%PDF-"
        ):
            raise ValueError(
                "The uploaded PDF does not contain a valid PDF signature."
            )
        return

    if content_type in {
        "text/plain",
        "text/csv",
    }:
        try:
            file_bytes.decode(
                "utf-8"
            )
        except UnicodeDecodeError as error:
            raise ValueError(
                "Text evidence must be valid UTF-8 text."
            ) from error
        return

    if content_type == "application/json":
        try:
            decoded = file_bytes.decode(
                "utf-8"
            )
            json.loads(
                decoded
            )
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as error:
            raise ValueError(
                "JSON evidence must contain valid UTF-8 JSON."
            ) from error
        return

    raise ValueError(
        "This evidence file type is not supported."
    )
