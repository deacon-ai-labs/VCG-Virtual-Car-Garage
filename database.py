import os

from supabase import Client, create_client


def get_supabase_client() -> Client:
    """Create and return a Supabase client."""

    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_KEY must be configured."
        )

    return create_client(supabase_url, supabase_key)


def get_vehicles() -> list[dict]:
    """Return all vehicles ordered by profile name."""

    client = get_supabase_client()

    response = (
        client.table("vehicles")
        .select("*")
        .order("profile_name")
        .execute()
    )

    return response.data


def get_vehicle(vehicle_id: int) -> dict | None:
    """Return one vehicle by ID, or None if it does not exist."""

    client = get_supabase_client()

    response = (
        client.table("vehicles")
        .select("*")
        .eq("id", vehicle_id)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def add_vehicle(vehicle: dict) -> dict:
    """Insert one vehicle and return the saved database row."""

    client = get_supabase_client()

    response = (
        client.table("vehicles")
        .insert(vehicle)
        .select("*")
        .execute()
    )

    if not response.data:
        raise RuntimeError("Supabase did not return the saved vehicle.")

    return response.data[0]


def update_vehicle(vehicle_id: int, vehicle: dict) -> dict:
    """Update an existing vehicle and return the updated row."""

    client = get_supabase_client()

    response = (
        client.table("vehicles")
        .update(vehicle)
        .eq("id", vehicle_id)
        .select("*")
        .execute()
    )

    if not response.data:
        raise RuntimeError("Supabase did not return the updated vehicle.")

    return response.data[0]


def delete_vehicle(vehicle_id: int) -> None:
    """Delete a vehicle."""

    client = get_supabase_client()

    (
        client.table("vehicles")
        .delete()
        .eq("id", vehicle_id)
        .execute()
    )