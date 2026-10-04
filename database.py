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



def get_vehicle_components(
    client: Client,
    vehicle_id: int,
) -> list[dict]:
    """Return structured digital-twin components for one vehicle."""

    response = (
        client.table("vehicle_components")
        .select("*")
        .eq("vehicle_id", vehicle_id)
        .order("sort_order")
        .execute()
    )

    return response.data or []


def get_vehicle_specifications(
    client: Client,
    vehicle_id: int,
) -> list[dict]:
    """Return current structured specifications for one vehicle."""

    response = (
        client.table("vehicle_specifications")
        .select("*")
        .eq("vehicle_id", vehicle_id)
        .eq("is_current", True)
        .order("label")
        .execute()
    )

    return response.data or []


def get_vehicle_component_events(
    client: Client,
    vehicle_id: int,
) -> list[dict]:
    """Return component lifecycle events for one vehicle, newest first."""

    response = (
        client.table("vehicle_component_events")
        .select("*")
        .eq("vehicle_id", vehicle_id)
        .order(
            "occurred_at",
            desc=True,
        )
        .execute()
    )

    return response.data or []


def add_vehicle_component(
    client: Client,
    owner_id: str,
    vehicle_id: int,
    component: dict,
) -> dict:
    """Create one structured vehicle component."""

    component_data = dict(
        component
    )
    component_data["owner_id"] = (
        owner_id
    )
    component_data["vehicle_id"] = (
        vehicle_id
    )

    response = (
        client.table("vehicle_components")
        .insert(component_data)
        .select("*")
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Supabase did not return the saved vehicle component."
        )

    return response.data[0]


def update_vehicle_component(
    client: Client,
    component_id: str,
    changes: dict,
) -> dict:
    """Update one visible structured vehicle component."""

    component_changes = dict(
        changes
    )
    component_changes["updated_at"] = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    response = (
        client.table("vehicle_components")
        .update(component_changes)
        .eq(
            "id",
            component_id,
        )
        .select("*")
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Supabase did not return the updated vehicle component."
        )

    return response.data[0]


def add_vehicle_component_event(
    client: Client,
    owner_id: str,
    vehicle_id: int,
    component_id: str,
    event_type: str,
    notes: str | None = None,
    mileage: int | None = None,
) -> dict:
    """Record one lifecycle or catalogue event for a component."""

    event_data = {
        "owner_id": owner_id,
        "vehicle_id": vehicle_id,
        "component_id": component_id,
        "event_type": event_type,
        "notes": notes,
        "mileage": mileage,
    }

    response = (
        client.table(
            "vehicle_component_events"
        )
        .insert(event_data)
        .select("*")
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Supabase did not return the saved component event."
        )

    return response.data[0]


def get_maintenance_records(
    client: Client,
    vehicle_id: int,
) -> list[dict]:
    """Return append-only maintenance history for one vehicle."""

    response = (
        client.table(
            "maintenance_records"
        )
        .select("*")
        .eq(
            "vehicle_id",
            vehicle_id,
        )
        .order(
            "performed_at",
            desc=True,
        )
        .execute()
    )

    return response.data or []


def complete_maintenance_item(
    client: Client,
    item_id: str,
    performed_at,
    performed_mileage: int | None = None,
    cost_gbp: float | None = None,
    provider: str | None = None,
    notes: str | None = None,
    evidence_reference: str | None = None,
):
    """Atomically record completed work and advance recurring schedules."""

    response = (
        client.rpc(
            "complete_maintenance_item",
            {
                "p_item_id": item_id,
                "p_performed_at": performed_at.isoformat(),
                "p_performed_mileage": performed_mileage,
                "p_cost_gbp": cost_gbp,
                "p_provider": provider,
                "p_notes": notes,
                "p_evidence_reference": evidence_reference,
            },
        )
        .execute()
    )

    return response.data


def record_maintenance_history(
    client: Client,
    vehicle_id: int,
    title: str,
    category: str,
    performed_at,
    performed_mileage: int | None = None,
    cost_gbp: float | None = None,
    provider: str | None = None,
    notes: str | None = None,
    evidence_reference: str | None = None,
    twin_component_id: str | None = None,
):
    """Atomically add historic work and optional component lifecycle evidence."""

    response = (
        client.rpc(
            "record_maintenance_history",
            {
                "p_vehicle_id": vehicle_id,
                "p_title": title,
                "p_category": category,
                "p_performed_at": performed_at.isoformat(),
                "p_performed_mileage": performed_mileage,
                "p_cost_gbp": cost_gbp,
                "p_provider": provider,
                "p_notes": notes,
                "p_evidence_reference": evidence_reference,
                "p_twin_component_id": twin_component_id,
            },
        )
        .execute()
    )

    return response.data


def get_build_plan_items(
    client: Client,
    vehicle_id: int,
) -> list[dict]:
    """Return build-plan items for one visible vehicle."""

    response = (
        client.table(
            "vehicle_build_plan_items"
        )
        .select("*")
        .eq(
            "vehicle_id",
            vehicle_id,
        )
        .order(
            "sort_order"
        )
        .execute()
    )

    return response.data or []


def create_build_plan_install(
    client: Client,
    vehicle_id: int,
    parent_system_id: str,
    name: str,
    manufacturer: str | None = None,
    part_number: str | None = None,
    weight_kg: float | None = None,
    is_oem: bool | None = None,
    plan_status: str = "planned",
    priority: str = "normal",
    estimated_cost_gbp: float | None = None,
    compatibility_status: str = "unknown",
    compatibility_notes: str | None = None,
    target_date=None,
    notes: str | None = None,
):
    """Atomically create a planned component and installation plan."""

    response = (
        client.rpc(
            "create_build_plan_install",
            {
                "p_vehicle_id": vehicle_id,
                "p_parent_system_id": parent_system_id,
                "p_name": name,
                "p_manufacturer": manufacturer,
                "p_part_number": part_number,
                "p_weight_kg": weight_kg,
                "p_is_oem": is_oem,
                "p_plan_status": plan_status,
                "p_priority": priority,
                "p_estimated_cost_gbp": estimated_cost_gbp,
                "p_compatibility_status": compatibility_status,
                "p_compatibility_notes": compatibility_notes,
                "p_target_date": (
                    target_date.isoformat()
                    if target_date
                    else None
                ),
                "p_notes": notes,
            },
        )
        .execute()
    )

    return response.data


def create_build_plan_removal(
    client: Client,
    component_id: str,
    plan_status: str = "planned",
    priority: str = "normal",
    estimated_cost_gbp: float | None = None,
    target_date=None,
    notes: str | None = None,
):
    """Atomically create a removal plan for an installed component."""

    response = (
        client.rpc(
            "create_build_plan_removal",
            {
                "p_component_id": component_id,
                "p_plan_status": plan_status,
                "p_priority": priority,
                "p_estimated_cost_gbp": estimated_cost_gbp,
                "p_target_date": (
                    target_date.isoformat()
                    if target_date
                    else None
                ),
                "p_notes": notes,
            },
        )
        .execute()
    )

    return response.data


def update_build_plan_item(
    client: Client,
    plan_item_id: str,
    changes: dict,
) -> dict:
    """Update editable planning metadata without changing the physical action."""

    allowed_fields = {
        "status",
        "priority",
        "estimated_cost_gbp",
        "compatibility_status",
        "compatibility_notes",
        "target_date",
        "notes",
        "sort_order",
    }

    plan_changes = {
        key: value
        for key, value in changes.items()
        if key in allowed_fields
    }

    plan_changes[
        "updated_at"
    ] = datetime.now(
        timezone.utc
    ).isoformat()

    response = (
        client.table(
            "vehicle_build_plan_items"
        )
        .update(
            plan_changes
        )
        .eq(
            "id",
            plan_item_id,
        )
        .select("*")
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Supabase did not return the updated build plan."
        )

    return response.data[0]


def complete_build_plan_item(
    client: Client,
    plan_item_id: str,
    completed_at,
    mileage: int | None = None,
    actual_cost_gbp: float | None = None,
    notes: str | None = None,
):
    """Atomically apply a planned install/removal to the physical twin."""

    response = (
        client.rpc(
            "complete_build_plan_item",
            {
                "p_plan_item_id": plan_item_id,
                "p_completed_at": completed_at.isoformat(),
                "p_mileage": mileage,
                "p_actual_cost_gbp": actual_cost_gbp,
                "p_notes": notes,
            },
        )
        .execute()
    )

    return response.data


def cancel_build_plan_item(
    client: Client,
    plan_item_id: str,
    notes: str | None = None,
):
    """Cancel an active plan without altering an installed component."""

    response = (
        client.rpc(
            "cancel_build_plan_item",
            {
                "p_plan_item_id": plan_item_id,
                "p_notes": notes,
            },
        )
        .execute()
    )

    return response.data



def get_diagnostic_cases(
    client: Client,
    vehicle_id: int,
) -> list[dict]:
    """Return diagnostic cases for one vehicle, newest activity first."""

    response = (
        client.table(
            "diagnostic_cases"
        )
        .select("*")
        .eq(
            "vehicle_id",
            vehicle_id,
        )
        .order(
            "updated_at",
            desc=True,
        )
        .execute()
    )

    return response.data or []


def get_diagnostic_hypotheses(
    client: Client,
    vehicle_id: int,
) -> list[dict]:
    """Return diagnostic hypotheses for one vehicle."""

    response = (
        client.table(
            "diagnostic_hypotheses"
        )
        .select("*")
        .eq(
            "vehicle_id",
            vehicle_id,
        )
        .order(
            "sort_order"
        )
        .execute()
    )

    return response.data or []


def get_diagnostic_checks(
    client: Client,
    vehicle_id: int,
) -> list[dict]:
    """Return diagnostic checks for one vehicle."""

    response = (
        client.table(
            "diagnostic_checks"
        )
        .select("*")
        .eq(
            "vehicle_id",
            vehicle_id,
        )
        .order(
            "sort_order"
        )
        .execute()
    )

    return response.data or []


def add_diagnostic_case(
    client: Client,
    owner_id: str,
    vehicle_id: int,
    case_data: dict,
) -> dict:
    """Create one diagnostic investigation."""

    payload = dict(
        case_data
    )
    payload[
        "owner_id"
    ] = owner_id
    payload[
        "vehicle_id"
    ] = vehicle_id

    response = (
        client.table(
            "diagnostic_cases"
        )
        .insert(
            payload
        )
        .select("*")
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Supabase did not return the diagnostic case."
        )

    return response.data[0]


def update_diagnostic_case(
    client: Client,
    case_id: str,
    changes: dict,
) -> dict:
    """Update editable diagnostic-case fields."""

    allowed_fields = {
        "title",
        "symptom_description",
        "status",
        "priority",
        "drive_risk",
        "onset_date",
        "onset_mileage",
        "operating_conditions",
        "resolution_summary",
        "resolved_at",
    }

    payload = {
        key: value
        for key, value in changes.items()
        if key in allowed_fields
    }

    response = (
        client.table(
            "diagnostic_cases"
        )
        .update(
            payload
        )
        .eq(
            "id",
            case_id,
        )
        .select("*")
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Supabase did not return the updated diagnostic case."
        )

    return response.data[0]


def delete_diagnostic_case(
    client: Client,
    case_id: str,
) -> None:
    """Delete a diagnostic case and its cascading investigation records."""

    (
        client.table(
            "diagnostic_cases"
        )
        .delete()
        .eq(
            "id",
            case_id,
        )
        .execute()
    )


def add_diagnostic_hypothesis(
    client: Client,
    owner_id: str,
    vehicle_id: int,
    case_id: str,
    hypothesis_data: dict,
) -> dict:
    """Create a hypothesis inside one diagnostic case."""

    payload = dict(
        hypothesis_data
    )
    payload.update(
        {
            "owner_id": owner_id,
            "vehicle_id": vehicle_id,
            "case_id": case_id,
        }
    )

    response = (
        client.table(
            "diagnostic_hypotheses"
        )
        .insert(
            payload
        )
        .select("*")
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Supabase did not return the diagnostic hypothesis."
        )

    return response.data[0]


def update_diagnostic_hypothesis(
    client: Client,
    hypothesis_id: str,
    changes: dict,
) -> dict:
    """Update editable hypothesis fields."""

    allowed_fields = {
        "component_id",
        "title",
        "rationale",
        "status",
        "source_kind",
        "sort_order",
    }

    payload = {
        key: value
        for key, value in changes.items()
        if key in allowed_fields
    }

    response = (
        client.table(
            "diagnostic_hypotheses"
        )
        .update(
            payload
        )
        .eq(
            "id",
            hypothesis_id,
        )
        .select("*")
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Supabase did not return the updated diagnostic hypothesis."
        )

    return response.data[0]


def delete_diagnostic_hypothesis(
    client: Client,
    hypothesis_id: str,
) -> None:
    """Delete a hypothesis; linked checks remain as case evidence."""

    (
        client.table(
            "diagnostic_hypotheses"
        )
        .delete()
        .eq(
            "id",
            hypothesis_id,
        )
        .execute()
    )


def add_diagnostic_check(
    client: Client,
    owner_id: str,
    vehicle_id: int,
    case_id: str,
    check_data: dict,
) -> dict:
    """Create a planned diagnostic check."""

    payload = dict(
        check_data
    )
    payload.update(
        {
            "owner_id": owner_id,
            "vehicle_id": vehicle_id,
            "case_id": case_id,
        }
    )

    response = (
        client.table(
            "diagnostic_checks"
        )
        .insert(
            payload
        )
        .select("*")
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Supabase did not return the diagnostic check."
        )

    return response.data[0]


def update_diagnostic_check(
    client: Client,
    check_id: str,
    changes: dict,
) -> dict:
    """Update editable diagnostic-check fields."""

    allowed_fields = {
        "hypothesis_id",
        "component_id",
        "title",
        "check_type",
        "procedure",
        "safety_notes",
        "status",
        "outcome",
        "finding",
        "performed_at",
        "performed_mileage",
        "sort_order",
    }

    payload = {
        key: value
        for key, value in changes.items()
        if key in allowed_fields
    }

    response = (
        client.table(
            "diagnostic_checks"
        )
        .update(
            payload
        )
        .eq(
            "id",
            check_id,
        )
        .select("*")
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Supabase did not return the updated diagnostic check."
        )

    return response.data[0]


def delete_diagnostic_check(
    client: Client,
    check_id: str,
) -> None:
    """Delete one diagnostic check."""

    (
        client.table(
            "diagnostic_checks"
        )
        .delete()
        .eq(
            "id",
            check_id,
        )
        .execute()
    )
