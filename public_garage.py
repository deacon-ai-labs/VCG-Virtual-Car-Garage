from __future__ import annotations

import re


GARAGE_THEMES = (
    ("midnight", "Midnight"),
    ("concrete", "Concrete"),
    ("studio", "Clean Studio"),
    ("neon", "Neon Bay"),
)

THEME_KEYS = {
    key
    for key, _label in GARAGE_THEMES
}

RESERVED_GARAGE_SLUGS = {
    "admin",
    "api",
    "app",
    "auth",
    "garage",
    "login",
    "privacy",
    "settings",
    "signup",
}


def normalize_public_slug(
    value: str | None,
) -> str:
    raw = str(
        value
        or ""
    ).strip().lower()

    raw = re.sub(
        r"[\s_]+",
        "-",
        raw,
    )
    raw = re.sub(
        r"[^a-z0-9-]",
        "",
        raw,
    )
    raw = re.sub(
        r"-+",
        "-",
        raw,
    ).strip("-")

    return raw[
        :32
    ]


def public_slug_error(
    value: str | None,
) -> str | None:
    slug = normalize_public_slug(
        value
    )

    if len(
        slug
    ) < 3:
        return (
            "Public garage link must contain at least 3 letters/numbers."
        )

    if slug in RESERVED_GARAGE_SLUGS:
        return (
            "That public garage link is reserved. Choose another."
        )

    if not re.fullmatch(
        r"[a-z0-9][a-z0-9-]{2,31}",
        slug,
    ):
        return (
            "Use only letters, numbers and hyphens in the public garage link."
        )

    return None


def normalize_theme(
    value: str | None,
) -> str:
    theme = str(
        value
        or "midnight"
    )

    if theme not in THEME_KEYS:
        return "midnight"

    return theme


def public_vehicle_defaults(
    vehicle_id: int,
    owner_id: str,
) -> dict:
    return {
        "vehicle_id": vehicle_id,
        "owner_id": owner_id,
        "is_public": False,
        "show_photo": True,
        "show_year": True,
        "show_manufacturer": True,
        "show_model": True,
        "show_engine": False,
        "show_mileage": False,
        "show_modifications": False,
        "show_specifications": False,
        "public_bio": None,
        "public_photo_path": None,
        "sort_order": 0,
    }
