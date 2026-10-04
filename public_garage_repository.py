from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from supabase import Client

from public_garage import (
    normalize_public_slug,
    normalize_theme,
    public_vehicle_defaults,
)
from upload_security import (
    validate_vehicle_photo_upload,
)


PRIVATE_PHOTO_BUCKET = "vehicle-photos"
PUBLIC_GARAGE_BUCKET = "public-garage"

PHOTO_CONTENT_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


def get_public_garage_settings(
    client: Client,
    owner_id: str,
) -> dict | None:
    response = (
        client.table(
            "public_garages"
        )
        .select("*")
        .eq(
            "owner_id",
            owner_id,
        )
        .limit(
            1
        )
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def upsert_public_garage_settings(
    client: Client,
    owner_id: str,
    settings: dict,
) -> dict:
    payload = {
        "owner_id": owner_id,
        "slug": normalize_public_slug(
            settings.get(
                "slug"
            )
        ),
        "display_name": str(
            settings.get(
                "display_name"
            )
            or "My Garage"
        ).strip(),
        "bio": (
            str(
                settings.get(
                    "bio"
                )
                or ""
            ).strip()
            or None
        ),
        "theme": normalize_theme(
            settings.get(
                "theme"
            )
        ),
        "is_public": bool(
            settings.get(
                "is_public"
            )
        ),
    }

    response = (
        client.table(
            "public_garages"
        )
        .upsert(
            payload,
            on_conflict="owner_id",
        )
        .select("*")
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Supabase did not return the public garage settings."
        )

    return response.data[0]


def get_public_vehicle_profiles(
    client: Client,
    owner_id: str,
) -> list[dict]:
    response = (
        client.table(
            "public_vehicle_profiles"
        )
        .select("*")
        .eq(
            "owner_id",
            owner_id,
        )
        .order(
            "sort_order"
        )
        .execute()
    )

    return response.data or []


def upsert_public_vehicle_profile(
    client: Client,
    owner_id: str,
    vehicle_id: int,
    changes: dict,
    existing: dict | None = None,
) -> dict:
    payload = public_vehicle_defaults(
        vehicle_id,
        owner_id,
    )

    if existing:
        payload.update(
            {
                key: existing.get(
                    key
                )
                for key in payload
                if key in existing
            }
        )

    for key in (
        "is_public",
        "show_photo",
        "show_year",
        "show_manufacturer",
        "show_model",
        "show_engine",
        "show_mileage",
        "show_modifications",
        "show_specifications",
        "sort_order",
    ):
        if key in changes:
            payload[
                key
            ] = changes[
                key
            ]

    if "public_bio" in changes:
        payload[
            "public_bio"
        ] = (
            str(
                changes.get(
                    "public_bio"
                )
                or ""
            ).strip()
            or None
        )

    if existing:
        payload[
            "public_photo_path"
        ] = existing.get(
            "public_photo_path"
        )

    response = (
        client.table(
            "public_vehicle_profiles"
        )
        .upsert(
            payload,
            on_conflict="vehicle_id",
        )
        .select("*")
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Supabase did not return the public vehicle settings."
        )

    return response.data[0]


def _public_photo_content_type(
    photo_path: str,
) -> str:
    suffix = Path(
        photo_path
    ).suffix.lower()

    content_type = PHOTO_CONTENT_TYPES.get(
        suffix
    )

    if not content_type:
        raise ValueError(
            "Only JPG, PNG and WEBP vehicle photos can be published."
        )

    return content_type


def publish_vehicle_photo_copy(
    client: Client,
    owner_id: str,
    vehicle: dict,
    public_profile: dict,
) -> dict:
    source_path = vehicle.get(
        "photo_path"
    )

    if not source_path:
        raise ValueError(
            "Add a vehicle photo before publishing it."
        )

    content_type = _public_photo_content_type(
        source_path
    )

    downloaded = (
        client.storage
        .from_(
            PRIVATE_PHOTO_BUCKET
        )
        .download(
            source_path
        )
    )

    file_bytes = (
        downloaded
        if isinstance(
            downloaded,
            bytes,
        )
        else bytes(
            downloaded
        )
    )

    validate_vehicle_photo_upload(
        file_bytes,
        content_type,
    )

    suffix = Path(
        source_path
    ).suffix.lower()

    new_path = (
        f"{uuid4().hex}{suffix}"
    )

    (
        client.storage
        .from_(
            PUBLIC_GARAGE_BUCKET
        )
        .upload(
            path=new_path,
            file=file_bytes,
            file_options={
                "content-type": content_type,
                "upsert": "false",
            },
        )
    )

    try:
        response = (
            client.table(
                "public_vehicle_profiles"
            )
            .update(
                {
                    "public_photo_path": new_path,
                }
            )
            .eq(
                "vehicle_id",
                vehicle[
                    "id"
                ],
            )
            .select("*")
            .execute()
        )

        if not response.data:
            raise RuntimeError(
                "Supabase did not return the published vehicle profile."
            )
    except Exception:
        (
            client.storage
            .from_(
                PUBLIC_GARAGE_BUCKET
            )
            .remove(
                [
                    new_path
                ]
            )
        )
        raise

    return response.data[0]


def revoke_public_vehicle_photo(
    client: Client,
    vehicle_id: int,
) -> dict | None:
    response = (
        client.table(
            "public_vehicle_profiles"
        )
        .update(
            {
                "public_photo_path": None,
            }
        )
        .eq(
            "vehicle_id",
            vehicle_id,
        )
        .select("*")
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def sync_public_vehicle_photo(
    client: Client,
    owner_id: str,
    vehicle: dict,
    public_profile: dict,
    garage_is_public: bool,
) -> dict:
    should_publish = (
        garage_is_public
        and bool(
            public_profile.get(
                "is_public"
            )
        )
        and bool(
            public_profile.get(
                "show_photo"
            )
        )
        and bool(
            vehicle.get(
                "photo_path"
            )
        )
    )

    if (
        should_publish
        and public_profile.get(
            "public_photo_path"
        )
    ):
        return public_profile

    if should_publish:
        return publish_vehicle_photo_copy(
            client,
            owner_id,
            vehicle,
            public_profile,
        )

    if public_profile.get(
        "public_photo_path"
    ):
        revoked = revoke_public_vehicle_photo(
            client,
            vehicle[
                "id"
            ],
        )

        if revoked:
            return revoked

    return public_profile


def _public_components(
    client: Client,
    vehicle_id: int,
) -> list[dict]:
    response = (
        client.table(
            "vehicle_components"
        )
        .select(
            "name,manufacturer,part_number,system_key,position,sort_order"
        )
        .eq(
            "vehicle_id",
            vehicle_id,
        )
        .eq(
            "component_type",
            "component",
        )
        .eq(
            "lifecycle_status",
            "installed",
        )
        .order(
            "sort_order"
        )
        .execute()
    )

    components = response.data or []

    return [
        {
            key: item.get(
                key
            )
            for key in (
                "name",
                "manufacturer",
                "part_number",
                "system_key",
                "position",
            )
            if item.get(
                key
            )
            is not None
        }
        for item in components
    ]


def _public_specifications(
    client: Client,
    vehicle_id: int,
) -> list[dict]:
    response = (
        client.table(
            "vehicle_specifications"
        )
        .select(
            "label,value_text,value_numeric,unit"
        )
        .eq(
            "vehicle_id",
            vehicle_id,
        )
        .eq(
            "is_current",
            True,
        )
        .order(
            "label"
        )
        .execute()
    )

    return response.data or []


def build_public_garage_payload(
    client: Client,
    garage: dict,
    vehicles: list[dict],
    profiles: list[dict],
) -> dict:
    vehicles_by_id = {
        int(
            vehicle[
                "id"
            ]
        ): vehicle
        for vehicle in vehicles
    }

    public_vehicles = []

    ordered_profiles = sorted(
        profiles,
        key=lambda item: (
            int(
                item.get(
                    "sort_order",
                    0,
                )
                or 0
            ),
            int(
                item[
                    "vehicle_id"
                ]
            ),
        ),
    )

    for profile in ordered_profiles:
        if not profile.get(
            "is_public"
        ):
            continue

        vehicle = vehicles_by_id.get(
            int(
                profile[
                    "vehicle_id"
                ]
            )
        )

        if not vehicle:
            continue

        vehicle_payload = {
            "profile_name": vehicle.get(
                "profile_name"
            ),
            "public_bio": profile.get(
                "public_bio"
            ),
            "year": (
                vehicle.get(
                    "year"
                )
                if profile.get(
                    "show_year"
                )
                else None
            ),
            "manufacturer": (
                vehicle.get(
                    "manufacturer"
                )
                if profile.get(
                    "show_manufacturer"
                )
                else None
            ),
            "model": (
                vehicle.get(
                    "model"
                )
                if profile.get(
                    "show_model"
                )
                else None
            ),
            "engine": (
                vehicle.get(
                    "engine"
                )
                if profile.get(
                    "show_engine"
                )
                else None
            ),
            "mileage": (
                vehicle.get(
                    "mileage"
                )
                if profile.get(
                    "show_mileage"
                )
                else None
            ),
            "public_photo_path": (
                profile.get(
                    "public_photo_path"
                )
                if profile.get(
                    "show_photo"
                )
                else None
            ),
            "installed_components": (
                _public_components(
                    client,
                    int(
                        vehicle[
                            "id"
                        ]
                    ),
                )
                if profile.get(
                    "show_modifications"
                )
                else []
            ),
            "specifications": (
                _public_specifications(
                    client,
                    int(
                        vehicle[
                            "id"
                        ]
                    ),
                )
                if profile.get(
                    "show_specifications"
                )
                else []
            ),
        }

        public_vehicles.append(
            vehicle_payload
        )

    return {
        "slug": garage.get(
            "slug"
        ),
        "display_name": garage.get(
            "display_name"
        ),
        "bio": garage.get(
            "bio"
        ),
        "theme": garage.get(
            "theme",
            "midnight",
        ),
        "vehicles": public_vehicles,
    }


def publish_public_garage_snapshot(
    client: Client,
    garage: dict | None,
    vehicles: list[dict],
    profiles: list[dict],
) -> dict | None:
    if not garage:
        return None

    slug = normalize_public_slug(
        garage.get(
            "slug"
        )
    )

    if not garage.get(
        "is_public"
    ):
        (
            client.table(
                "public_garage_snapshots"
            )
            .delete()
            .eq(
                "slug",
                slug,
            )
            .execute()
        )
        return None

    payload = build_public_garage_payload(
        client,
        garage,
        vehicles,
        profiles,
    )

    response = (
        client.table(
            "public_garage_snapshots"
        )
        .upsert(
            {
                "slug": slug,
                "payload": payload,
                "published_at": datetime.now(
                    timezone.utc
                ).isoformat(),
            },
            on_conflict="slug",
        )
        .select("*")
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Supabase did not return the published garage snapshot."
        )

    return response.data[0]


def get_public_snapshot(
    client: Client,
    slug: str,
) -> dict | None:
    response = (
        client.table(
            "public_garage_snapshots"
        )
        .select(
            "slug,published_at"
        )
        .eq(
            "slug",
            normalize_public_slug(
                slug
            ),
        )
        .limit(
            1
        )
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def ensure_public_garage_snapshot(
    client: Client,
    owner_id: str,
    vehicles: list[dict],
) -> None:
    garage = get_public_garage_settings(
        client,
        owner_id,
    )

    if (
        not garage
        or not garage.get(
            "is_public"
        )
    ):
        return

    existing_snapshot = get_public_snapshot(
        client,
        garage[
            "slug"
        ],
    )

    if existing_snapshot:
        return

    profiles = get_public_vehicle_profiles(
        client,
        owner_id,
    )

    profile_lookup = {
        int(
            profile[
                "vehicle_id"
            ]
        ): profile
        for profile in profiles
    }

    for vehicle in vehicles:
        profile = profile_lookup.get(
            int(
                vehicle[
                    "id"
                ]
            )
        )

        if not profile:
            continue

        sync_public_vehicle_photo(
            client=client,
            owner_id=owner_id,
            vehicle=vehicle,
            public_profile=profile,
            garage_is_public=True,
        )

    refreshed_profiles = get_public_vehicle_profiles(
        client,
        owner_id,
    )

    publish_public_garage_snapshot(
        client,
        garage,
        vehicles,
        refreshed_profiles,
    )


def fetch_public_garage(
    client: Client,
    slug: str,
) -> dict | None:
    response = (
        client.table(
            "public_garage_snapshots"
        )
        .select(
            "payload"
        )
        .eq(
            "slug",
            normalize_public_slug(
                slug
            ),
        )
        .limit(
            1
        )
        .execute()
    )

    if not response.data:
        return None

    return response.data[0].get(
        "payload"
    )


def public_photo_url(
    client: Client,
    storage_path: str | None,
) -> str | None:
    if not storage_path:
        return None

    response = (
        client.storage
        .from_(
            PUBLIC_GARAGE_BUCKET
        )
        .get_public_url(
            storage_path
        )
    )

    if isinstance(
        response,
        str,
    ):
        return response

    if isinstance(
        response,
        dict,
    ):
        return (
            response.get(
                "publicUrl"
            )
            or response.get(
                "publicURL"
            )
            or response.get(
                "public_url"
            )
        )

    return (
        getattr(
            response,
            "public_url",
            None,
        )
        or getattr(
            response,
            "publicUrl",
            None,
        )
    )
