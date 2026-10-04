from __future__ import annotations

import re


VEHICLE_SYSTEMS = (
    ("engine", "Engine"),
    ("intake_fuel", "Intake & Fuel"),
    ("cooling", "Cooling"),
    ("electrical", "Electrical"),
    ("transmission_driveline", "Transmission & Driveline"),
    ("suspension_steering", "Suspension & Steering"),
    ("brakes", "Brakes"),
    ("wheels_tyres", "Wheels & Tyres"),
    ("interior_safety", "Interior & Safety"),
    ("exhaust", "Exhaust"),
    ("body_exterior", "Body & Exterior"),
    ("fluids_consumables", "Fluids & Consumables"),
)

SYSTEM_KEYS = {
    key
    for key, _label in VEHICLE_SYSTEMS
}

CONFIDENCE_LEVELS = {
    "verified",
    "high",
    "medium",
    "low",
    "unknown",
}


def normalize_registration(
    value: str | None,
) -> str | None:
    if not value:
        return None

    clean = re.sub(
        r"[^A-Za-z0-9]",
        "",
        value,
    ).upper()

    return clean or None


def normalize_vin(
    value: str | None,
) -> str | None:
    if not value:
        return None

    clean = re.sub(
        r"[^A-Za-z0-9]",
        "",
        value,
    ).upper()

    return clean or None


def normalize_component_candidate(
    candidate: dict,
) -> dict:
    """Return only supported component-candidate fields."""

    name = str(
        candidate.get(
            "name"
        )
        or ""
    ).strip()

    if not name:
        raise ValueError(
            "Candidate component requires a name."
        )

    system_key = str(
        candidate.get(
            "system_key"
        )
        or ""
    ).strip()

    if system_key not in SYSTEM_KEYS:
        raise ValueError(
            "Candidate component requires a valid vehicle system."
        )

    confidence = str(
        candidate.get(
            "confidence"
        )
        or "unknown"
    ).lower()

    if confidence not in CONFIDENCE_LEVELS:
        confidence = "unknown"

    # Extraction is never allowed to self-verify a fact.
    if confidence in {
        "verified",
        "high",
    }:
        confidence = "medium"

    def optional_text(
        key: str,
    ) -> str | None:
        value = candidate.get(
            key
        )

        if value is None:
            return None

        clean = str(
            value
        ).strip()

        return clean or None

    is_oem = candidate.get(
        "is_oem"
    )

    if is_oem not in {
        True,
        False,
        None,
    }:
        is_oem = None

    return {
        "name": name,
        "system_key": system_key,
        "manufacturer": optional_text(
            "manufacturer"
        ),
        "part_number": optional_text(
            "part_number"
        ),
        "position": optional_text(
            "position"
        ),
        "notes": optional_text(
            "notes"
        ),
        "is_oem": is_oem,
        "confidence": confidence,
    }


def intake_snapshot(
    vehicle: dict,
    evidence: list[dict],
    candidates: list[dict],
) -> dict:
    pending = [
        item
        for item in candidates
        if item.get(
            "review_status"
        )
        == "pending"
    ]
    approved = [
        item
        for item in candidates
        if item.get(
            "review_status"
        )
        == "approved"
    ]
    rejected = [
        item
        for item in candidates
        if item.get(
            "review_status"
        )
        == "rejected"
    ]

    return {
        "status": vehicle.get(
            "intake_status",
            "complete",
        ),
        "registration": vehicle.get(
            "registration"
        ),
        "vin": vehicle.get(
            "vin"
        ),
        "evidence_count": len(
            evidence
        ),
        "pending_count": len(
            pending
        ),
        "approved_count": len(
            approved
        ),
        "rejected_count": len(
            rejected
        ),
        "can_complete": not pending,
    }
