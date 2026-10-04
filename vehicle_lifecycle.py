from __future__ import annotations

from supabase import Client


VEHICLE_PHOTO_BUCKET = "vehicle-photos"
VEHICLE_EVIDENCE_BUCKET = "vehicle-evidence"


def _asset_rows(
    owner_id: str,
    vehicle: dict,
    evidence: list[dict],
) -> list[dict]:
    rows = []

    photo_path = vehicle.get(
        "photo_path"
    )

    if photo_path:
        rows.append(
            {
                "owner_id": owner_id,
                "bucket_id": VEHICLE_PHOTO_BUCKET,
                "storage_path": photo_path,
                "reason": "vehicle_delete",
            }
        )

    for item in evidence:
        storage_path = item.get(
            "storage_path"
        )

        if not storage_path:
            continue

        rows.append(
            {
                "owner_id": owner_id,
                "bucket_id": VEHICLE_EVIDENCE_BUCKET,
                "storage_path": storage_path,
                "reason": "vehicle_delete",
            }
        )

    unique = {}

    for row in rows:
        key = (
            row[
                "bucket_id"
            ],
            row[
                "storage_path"
            ],
        )
        unique[
            key
        ] = row

    return list(
        unique.values()
    )


def queue_vehicle_asset_cleanup(
    client: Client,
    owner_id: str,
    vehicle: dict,
    evidence: list[dict],
) -> int:
    rows = _asset_rows(
        owner_id,
        vehicle,
        evidence,
    )

    if not rows:
        return 0

    (
        client.table(
            "storage_cleanup_queue"
        )
        .upsert(
            rows,
            on_conflict=(
                "owner_id,bucket_id,storage_path"
            ),
        )
        .execute()
    )

    return len(
        rows
    )


def process_pending_storage_cleanup(
    client: Client,
    owner_id: str,
    limit: int = 100,
) -> dict:
    response = (
        client.table(
            "storage_cleanup_queue"
        )
        .select("*")
        .eq(
            "owner_id",
            owner_id,
        )
        .order(
            "created_at"
        )
        .limit(
            limit
        )
        .execute()
    )

    queued = response.data or []
    removed = 0
    failed = 0

    for item in queued:
        try:
            (
                client.storage
                .from_(
                    item[
                        "bucket_id"
                    ]
                )
                .remove(
                    [
                        item[
                            "storage_path"
                        ]
                    ]
                )
            )

            (
                client.table(
                    "storage_cleanup_queue"
                )
                .delete()
                .eq(
                    "id",
                    item[
                        "id"
                    ],
                )
                .execute()
            )

            removed += 1
        except Exception as error:
            failed += 1

            (
                client.table(
                    "storage_cleanup_queue"
                )
                .update(
                    {
                        "attempts": int(
                            item.get(
                                "attempts",
                                0,
                            )
                            or 0
                        )
                        + 1,
                        "last_error_type": type(
                            error
                        ).__name__,
                    }
                )
                .eq(
                    "id",
                    item[
                        "id"
                    ],
                )
                .execute()
            )

    return {
        "queued": len(
            queued
        ),
        "removed": removed,
        "failed": failed,
    }


def delete_vehicle_with_assets(
    client: Client,
    owner_id: str,
    vehicle: dict,
    evidence: list[dict],
) -> dict:
    queue_vehicle_asset_cleanup(
        client,
        owner_id,
        vehicle,
        evidence,
    )

    (
        client.rpc(
            "delete_vehicle_for_cleanup",
            {
                "p_vehicle_id": vehicle[
                    "id"
                ],
            },
        )
        .execute()
    )

    return process_pending_storage_cleanup(
        client,
        owner_id,
    )
