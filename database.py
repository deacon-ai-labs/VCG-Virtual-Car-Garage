import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from supabase import Client, create_client


def get_supabase_client() -> Client:
    """Create and return a Supabase client."""

    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_KEY must be configured."
        )

    return create_client(
        supabase_url,
        supabase_key,
    )


def get_vehicles(client: Client) -> list[dict]:
    """Return vehicles visible to the authenticated user."""

    response = (
        client.table("vehicles")
        .select("*")
        .order("profile_name")
        .execute()
    )

    return response.data or []


def get_vehicle(
    client: Client,
    vehicle_id: int,
) -> dict | None:
    """Return one visible vehicle by ID, or None."""

    response = (
        client.table("vehicles")
        .select("*")
        .eq("id", vehicle_id)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def add_vehicle(
    client: Client,
    owner_id: str,
    vehicle: dict,
) -> dict:
    """Insert one vehicle owned by the authenticated user."""

    vehicle_data = dict(vehicle)
    vehicle_data["owner_id"] = owner_id

    response = (
        client.table("vehicles")
        .insert(vehicle_data)
        .select("*")
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Supabase did not return the saved vehicle."
        )

    return response.data[0]


def update_vehicle(
    client: Client,
    vehicle_id: int,
    vehicle: dict,
) -> dict:
    """Update a visible vehicle and return the updated row."""

    response = (
        client.table("vehicles")
        .update(vehicle)
        .eq("id", vehicle_id)
        .select("*")
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Supabase did not return the updated vehicle."
        )

    return response.data[0]


def delete_vehicle(
    client: Client,
    vehicle_id: int,
) -> None:
    """Delete a visible vehicle."""

    (
        client.table("vehicles")
        .delete()
        .eq("id", vehicle_id)
        .execute()
    )


def get_conversations(
    client: Client,
    vehicle_id: int,
) -> list[dict]:
    """Return conversations for one visible vehicle, newest first."""

    response = (
        client.table("conversations")
        .select("*")
        .eq("vehicle_id", vehicle_id)
        .order("updated_at", desc=True)
        .execute()
    )

    return response.data or []


def create_conversation(
    client: Client,
    owner_id: str,
    vehicle_id: int,
    title: str,
) -> dict:
    """Create and return a new conversation."""

    conversation_data = {
        "owner_id": owner_id,
        "vehicle_id": vehicle_id,
        "title": title.strip() or "New conversation",
    }

    response = (
        client.table("conversations")
        .insert(conversation_data)
        .select("*")
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Supabase did not return the saved conversation."
        )

    return response.data[0]


def get_messages(
    client: Client,
    conversation_id: str,
) -> list[dict]:
    """Return messages for one visible conversation in time order."""

    response = (
        client.table("messages")
        .select("*")
        .eq("conversation_id", conversation_id)
        .order("created_at")
        .execute()
    )

    return response.data or []


def add_message(
    client: Client,
    owner_id: str,
    conversation_id: str,
    role: str,
    content: str,
) -> dict:
    """Save one user or assistant message."""

    message_data = {
        "conversation_id": conversation_id,
        "owner_id": owner_id,
        "role": role,
        "content": content,
    }

    response = (
        client.table("messages")
        .insert(message_data)
        .select("*")
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Supabase did not return the saved message."
        )

    return response.data[0]


def update_conversation_response_id(
    client: Client,
    conversation_id: str,
    response_id: str,
) -> None:
    """Store the latest OpenAI response ID for continuation."""

    updated_at = datetime.now(
        timezone.utc
    ).isoformat()

    (
        client.table("conversations")
        .update(
            {
                "last_response_id": response_id,
                "updated_at": updated_at,
            }
        )
        .eq("id", conversation_id)
        .execute()
    )

def rename_conversation(
    client: Client,
    conversation_id: str,
    title: str,
) -> dict:
    """Rename a visible conversation and return the updated row."""

    clean_title = title.strip()

    if not clean_title:
        raise ValueError(
            "Conversation title must not be empty."
        )

    response = (
        client.table("conversations")
        .update(
            {
                "title": clean_title,
            }
        )
        .eq("id", conversation_id)
        .select("*")
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Supabase did not return the renamed conversation."
        )

    return response.data[0]


def delete_conversation(
    client: Client,
    conversation_id: str,
) -> None:
    """Delete a visible conversation and its cascaded messages."""

    (
        client.table("conversations")
        .delete()
        .eq("id", conversation_id)
        .execute()
    )


VEHICLE_PHOTO_BUCKET = "vehicle-photos"
VEHICLE_PHOTO_URL_SECONDS = 3600
ALLOWED_PHOTO_SUFFIXES = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


def get_maintenance_items(
    client: Client,
    vehicle_id: int,
) -> list[dict]:
    """Return maintenance items for one visible vehicle."""

    response = (
        client.table("maintenance_items")
        .select("*")
        .eq("vehicle_id", vehicle_id)
        .order("sort_order")
        .execute()
    )

    return response.data or []


def add_maintenance_item(
    client: Client,
    owner_id: str,
    vehicle_id: int,
    item: dict,
) -> dict:
    """Create one maintenance item for a user's vehicle."""

    item_data = dict(item)
    item_data["owner_id"] = owner_id
    item_data["vehicle_id"] = vehicle_id

    response = (
        client.table("maintenance_items")
        .insert(item_data)
        .select("*")
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Supabase did not return the saved maintenance item."
        )

    return response.data[0]


def update_maintenance_item(
    client: Client,
    item_id: str,
    changes: dict,
) -> dict:
    """Update one visible maintenance item."""

    item_changes = dict(changes)
    item_changes["updated_at"] = datetime.now(
        timezone.utc
    ).isoformat()

    response = (
        client.table("maintenance_items")
        .update(item_changes)
        .eq("id", item_id)
        .select("*")
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Supabase did not return the updated maintenance item."
        )

    return response.data[0]


def delete_maintenance_item(
    client: Client,
    item_id: str,
) -> None:
    """Delete one visible maintenance item."""

    (
        client.table("maintenance_items")
        .delete()
        .eq("id", item_id)
        .execute()
    )


def set_maintenance_completed(
    client: Client,
    item_id: str,
    completed: bool,
) -> dict:
    """Mark a maintenance item completed or reopen it."""

    now = datetime.now(
        timezone.utc
    ).isoformat()

    changes = {
        "status": (
            "completed"
            if completed
            else "pending"
        ),
        "completed_at": (
            now
            if completed
            else None
        ),
        "updated_at": now,
    }

    response = (
        client.table("maintenance_items")
        .update(changes)
        .eq("id", item_id)
        .select("*")
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Supabase did not return the updated maintenance item."
        )

    return response.data[0]


def upload_vehicle_photo(
    client: Client,
    owner_id: str,
    vehicle_id: int,
    filename: str,
    file_bytes: bytes,
    content_type: str,
) -> str:
    """Upload a private vehicle photo and return its storage path."""

    suffix = Path(filename).suffix.lower()

    if suffix not in ALLOWED_PHOTO_SUFFIXES:
        raise ValueError(
            "Vehicle photo must be JPG, PNG, or WEBP."
        )

    if not content_type.startswith("image/"):
        raise ValueError(
            "Vehicle photo must use an image content type."
        )

    generated_name = (
        f"{uuid4().hex}{suffix}"
    )

    storage_path = (
        f"{owner_id}/"
        f"{vehicle_id}/"
        f"{generated_name}"
    )

    (
        client.storage
        .from_(VEHICLE_PHOTO_BUCKET)
        .upload(
            path=storage_path,
            file=file_bytes,
            file_options={
                "content-type": content_type,
                "upsert": "false",
            },
        )
    )

    return storage_path


def get_vehicle_photo_url(
    client: Client,
    photo_path: str | None,
    expires_in: int = VEHICLE_PHOTO_URL_SECONDS,
) -> str | None:
    """Return a temporary signed URL for a private vehicle photo."""

    if not photo_path:
        return None

    response = (
        client.storage
        .from_(VEHICLE_PHOTO_BUCKET)
        .create_signed_url(
            photo_path,
            expires_in,
        )
    )

    if isinstance(response, dict):
        return (
            response.get("signedURL")
            or response.get("signed_url")
            or response.get("signedUrl")
        )

    return (
        getattr(response, "signed_url", None)
        or getattr(response, "signedURL", None)
        or getattr(response, "signedUrl", None)
    )


def update_vehicle_photo_path(
    client: Client,
    vehicle_id: int,
    photo_path: str | None,
) -> dict:
    """Store or clear a vehicle's private photo path."""

    response = (
        client.table("vehicles")
        .update(
            {
                "photo_path": photo_path,
            }
        )
        .eq("id", vehicle_id)
        .select("*")
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Supabase did not return the updated vehicle."
        )

    return response.data[0]


def delete_vehicle_photo(
    client: Client,
    photo_path: str | None,
) -> None:
    """Delete a private vehicle photo if a path exists."""

    if not photo_path:
        return

    (
        client.storage
        .from_(VEHICLE_PHOTO_BUCKET)
        .remove(
            [photo_path]
        )
    )

