from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from supabase import Client


VEHICLE_EVIDENCE_BUCKET = "vehicle-evidence"
EVIDENCE_URL_SECONDS = 3600

ALLOWED_EVIDENCE_SUFFIXES = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".pdf",
    ".txt",
    ".csv",
    ".json",
}

ALLOWED_EVIDENCE_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/pdf",
    "text/plain",
    "text/csv",
    "application/json",
}


def get_vehicle_evidence(
    client: Client,
    vehicle_id: int,
) -> list[dict]:
    response = (
        client.table(
            "vehicle_evidence"
        )
        .select("*")
        .eq(
            "vehicle_id",
            vehicle_id,
        )
        .order(
            "created_at",
            desc=True,
        )
        .execute()
    )

    return response.data or []


def get_intake_candidates(
    client: Client,
    vehicle_id: int,
) -> list[dict]:
    response = (
        client.table(
            "vehicle_intake_candidates"
        )
        .select("*")
        .eq(
            "vehicle_id",
            vehicle_id,
        )
        .order(
            "created_at"
        )
        .execute()
    )

    return response.data or []


def upload_evidence_file(
    client: Client,
    owner_id: str,
    vehicle_id: int,
    filename: str,
    file_bytes: bytes,
    content_type: str,
) -> str:
    suffix = Path(
        filename
    ).suffix.lower()

    if suffix not in ALLOWED_EVIDENCE_SUFFIXES:
        raise ValueError(
            "Evidence must be JPG, PNG, WEBP, PDF, TXT, CSV, or JSON."
        )

    if content_type not in ALLOWED_EVIDENCE_CONTENT_TYPES:
        raise ValueError(
            "This evidence file type is not supported."
        )

    storage_path = (
        f"{owner_id}/"
        f"{vehicle_id}/"
        f"{uuid4().hex}{suffix}"
    )

    (
        client.storage
        .from_(
            VEHICLE_EVIDENCE_BUCKET
        )
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


def create_evidence_record(
    client: Client,
    owner_id: str,
    vehicle_id: int,
    evidence_data: dict,
) -> dict:
    payload = dict(
        evidence_data
    )
    payload[
        "owner_id"
    ] = owner_id
    payload[
        "vehicle_id"
    ] = vehicle_id

    response = (
        client.table(
            "vehicle_evidence"
        )
        .insert(
            payload
        )
        .select("*")
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Supabase did not return the evidence record."
        )

    return response.data[0]


def save_uploaded_evidence(
    client: Client,
    owner_id: str,
    vehicle_id: int,
    evidence_type: str,
    title: str,
    filename: str,
    file_bytes: bytes,
    content_type: str,
    notes: str | None = None,
) -> dict:
    storage_path = upload_evidence_file(
        client,
        owner_id,
        vehicle_id,
        filename,
        file_bytes,
        content_type,
    )

    try:
        return create_evidence_record(
            client,
            owner_id,
            vehicle_id,
            {
                "evidence_type": evidence_type,
                "title": title,
                "storage_path": storage_path,
                "original_filename": filename,
                "content_type": content_type,
                "source_kind": "user_upload",
                "notes": notes,
            },
        )
    except Exception:
        (
            client.storage
            .from_(
                VEHICLE_EVIDENCE_BUCKET
            )
            .remove(
                [
                    storage_path
                ]
            )
        )
        raise


def delete_evidence(
    client: Client,
    evidence: dict,
) -> None:
    storage_path = evidence.get(
        "storage_path"
    )

    (
        client.table(
            "vehicle_evidence"
        )
        .delete()
        .eq(
            "id",
            evidence[
                "id"
            ],
        )
        .execute()
    )

    if storage_path:
        (
            client.storage
            .from_(
                VEHICLE_EVIDENCE_BUCKET
            )
            .remove(
                [
                    storage_path
                ]
            )
        )


def get_evidence_url(
    client: Client,
    storage_path: str | None,
    expires_in: int = EVIDENCE_URL_SECONDS,
) -> str | None:
    if not storage_path:
        return None

    response = (
        client.storage
        .from_(
            VEHICLE_EVIDENCE_BUCKET
        )
        .create_signed_url(
            storage_path,
            expires_in,
        )
    )

    if isinstance(
        response,
        dict,
    ):
        return (
            response.get(
                "signedURL"
            )
            or response.get(
                "signed_url"
            )
            or response.get(
                "signedUrl"
            )
        )

    return (
        getattr(
            response,
            "signed_url",
            None,
        )
        or getattr(
            response,
            "signedURL",
            None,
        )
        or getattr(
            response,
            "signedUrl",
            None,
        )
    )


def create_intake_candidate(
    client: Client,
    owner_id: str,
    vehicle_id: int,
    candidate_kind: str,
    source_kind: str,
    payload: dict,
    confidence: str = "unknown",
    evidence_id: str | None = None,
    source_reference: str | None = None,
) -> dict:
    response = (
        client.table(
            "vehicle_intake_candidates"
        )
        .insert(
            {
                "owner_id": owner_id,
                "vehicle_id": vehicle_id,
                "evidence_id": evidence_id,
                "candidate_kind": candidate_kind,
                "source_kind": source_kind,
                "source_reference": source_reference,
                "confidence": confidence,
                "payload": payload,
            }
        )
        .select("*")
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Supabase did not return the intake candidate."
        )

    return response.data[0]


def update_intake_candidate(
    client: Client,
    candidate_id: str,
    payload: dict,
    confidence: str,
) -> dict:
    response = (
        client.table(
            "vehicle_intake_candidates"
        )
        .update(
            {
                "payload": payload,
                "confidence": confidence,
            }
        )
        .eq(
            "id",
            candidate_id,
        )
        .eq(
            "review_status",
            "pending",
        )
        .select("*")
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Only pending intake candidates can be edited."
        )

    return response.data[0]


def reject_intake_candidate(
    client: Client,
    candidate_id: str,
) -> dict:
    response = (
        client.table(
            "vehicle_intake_candidates"
        )
        .update(
            {
                "review_status": "rejected",
                "reviewed_at": datetime.now(
                    timezone.utc
                ).isoformat(),
            }
        )
        .eq(
            "id",
            candidate_id,
        )
        .eq(
            "review_status",
            "pending",
        )
        .select("*")
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Only pending intake candidates can be rejected."
        )

    return response.data[0]


def approve_component_candidate(
    client: Client,
    candidate_id: str,
) -> str:
    response = (
        client.rpc(
            "approve_vehicle_intake_component_candidate",
            {
                "p_candidate_id": candidate_id,
            },
        )
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "The approved component ID was not returned."
        )

    if isinstance(
        response.data,
        list,
    ):
        return str(
            response.data[0]
        )

    return str(
        response.data
    )


def mark_intake_complete(
    client: Client,
    vehicle_id: int,
):
    response = (
        client.rpc(
            "complete_vehicle_intake",
            {
                "p_vehicle_id": vehicle_id,
            },
        )
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Supabase did not return the completed vehicle intake."
        )

    return response.data


def reopen_intake(
    client: Client,
    vehicle_id: int,
) -> dict:
    response = (
        client.table(
            "vehicles"
        )
        .update(
            {
                "intake_status": "in_progress",
                "intake_completed_at": None,
            }
        )
        .eq(
            "id",
            vehicle_id,
        )
        .select("*")
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Supabase did not return the reopened vehicle intake."
        )

    return response.data[0]
