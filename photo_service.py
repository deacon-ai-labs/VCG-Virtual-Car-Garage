from database import (
    delete_vehicle_photo,
    update_vehicle_photo_path,
    upload_vehicle_photo,
)


def replace_vehicle_photo(
    client,
    owner_id: str,
    vehicle_id: int,
    old_photo_path: str | None,
    filename: str,
    file_bytes: bytes,
    content_type: str,
) -> str:
    """Upload a new photo, persist its path, then remove the old photo."""

    new_photo_path = upload_vehicle_photo(
        client,
        owner_id,
        vehicle_id,
        filename,
        file_bytes,
        content_type,
    )

    try:
        update_vehicle_photo_path(
            client,
            vehicle_id,
            new_photo_path,
        )
    except Exception:
        # Avoid leaving an orphaned newly uploaded object.
        delete_vehicle_photo(
            client,
            new_photo_path,
        )
        raise

    if (
        old_photo_path
        and old_photo_path != new_photo_path
    ):
        delete_vehicle_photo(
            client,
            old_photo_path,
        )

    return new_photo_path


def remove_vehicle_photo(
    client,
    vehicle_id: int,
    photo_path: str | None,
) -> None:
    """Clear the database path first, then remove the storage object."""

    if not photo_path:
        return

    update_vehicle_photo_path(
        client,
        vehicle_id,
        None,
    )

    delete_vehicle_photo(
        client,
        photo_path,
    )
