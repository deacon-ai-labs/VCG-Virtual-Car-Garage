import os
from datetime import datetime, timezone

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
        .order("created_at", desc=True)
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

