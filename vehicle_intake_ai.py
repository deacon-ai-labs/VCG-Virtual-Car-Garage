from __future__ import annotations

import json

from openai import OpenAI

from vehicle_intake import (
    VEHICLE_SYSTEMS,
    normalize_component_candidate,
)


client = OpenAI()


def extract_modification_candidates(
    modification_text: str,
    vehicle_description: str,
) -> list[dict]:
    """Extract only explicitly supported installed-component candidates."""

    clean_text = modification_text.strip()

    if not clean_text:
        return []

    system_reference = "\n".join(
        (
            f"- {key}: {label}"
            for key, label in VEHICLE_SYSTEMS
        )
    )

    response = client.responses.create(
        model="gpt-4.1-mini",
        instructions=(
            "You extract structured current-vehicle modification candidates "
            "for Virtual Car Garage. Do not diagnose, recommend, or infer "
            "unstated specifications. Extract only components the owner text "
            "explicitly says or very clearly implies are physically fitted. "
            "Do not turn future plans or wishes into installed components. "
            "Never invent a manufacturer, part number, weight, position, "
            "date, power figure, or technical specification. Unknown values "
            "must be null. Choose exactly one allowed system_key. "
            "Confidence must be medium, low, or unknown only. "
            "Return valid JSON only, in the shape "
            '{"components":[{"name":"...","system_key":"...",'
            '"manufacturer":null,"part_number":null,"position":null,'
            '"notes":null,"is_oem":null,"confidence":"medium"}]}. '
            "No markdown and no commentary.\n\n"
            "ALLOWED VEHICLE SYSTEMS:\n"
            f"{system_reference}\n\n"
            "The owner will review every candidate before it can modify "
            "the canonical digital twin."
        ),
        input=(
            "VEHICLE:\n"
            f"{vehicle_description}\n\n"
            "OWNER MODIFICATION DESCRIPTION:\n"
            f"{clean_text}"
        ),
    )

    try:
        parsed = json.loads(
            response.output_text
        )
    except (
        TypeError,
        json.JSONDecodeError,
    ) as error:
        raise ValueError(
            "Modification extraction did not return valid structured data."
        ) from error

    components = parsed.get(
        "components"
    )

    if not isinstance(
        components,
        list,
    ):
        raise ValueError(
            "Modification extraction returned an invalid component list."
        )

    normalized = []

    for component in components:
        if not isinstance(
            component,
            dict,
        ):
            continue

        normalized.append(
            normalize_component_candidate(
                component
            )
        )

    return normalized
