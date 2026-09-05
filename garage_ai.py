from openai import OpenAI

from rag import (
    format_knowledge_context,
    retrieve_knowledge,
)


client = OpenAI()


def infer_vehicle_scope(
    vehicle_description: str | None,
) -> str | None:
    """Map a selected vehicle to the matching RAG knowledge scope."""

    if not vehicle_description:
        return None

    description = vehicle_description.lower()

    is_civic = "civic" in description

    is_type_r = (
        "type r" in description
        or "type-r" in description
        or "typer" in description
        or "ep3" in description
    )

    if is_civic and is_type_r:
        return "civic_type_r_ep3"

    if is_civic:
        return "civic_3door_all_models"

    return None


def get_reference_context(
    user_message: str,
    vehicle_description: str | None,
) -> str:
    """Retrieve trusted documentation for the selected vehicle."""

    vehicle_scope = infer_vehicle_scope(
        vehicle_description
    )

    if vehicle_scope is None:
        return (
            "No matching vehicle-specific reference "
            "documents are available for the selected vehicle."
        )

    chunks = retrieve_knowledge(
        user_message,
        match_count=5,
        vehicle_scope=vehicle_scope,
    )

    return format_knowledge_context(
        chunks
    )


def ask_ai(
    user_message: str,
    vehicle_description: str | None,
    previous_response_id: str | None,
):
    """Send a grounded automotive question to Garage AI."""

    reference_context = get_reference_context(
        user_message,
        vehicle_description,
    )

    instructions = (
        "You are Virtual Car Garage's cautious automotive assistant. "
        "Help the user investigate automotive questions and problems. "
        "Do not claim certainty from limited information. "
        "Recommend only safe basic checks. "
        "Clearly state when a vehicle should not be driven or should "
        "be inspected by a qualified mechanic.\n\n"

        "SELECTED VEHICLE:\n"
        f"{vehicle_description or 'No vehicle is currently selected.'}\n\n"

        "REFERENCE MATERIAL:\n"
        f"{reference_context}\n\n"

        "GROUNDING AND SOURCE-AUTHORITY RULES:\n"
        "- Use the selected vehicle information whenever relevant.\n"
        "- Do not invent missing vehicle details.\n"
        "- Evidence labelled VEHICLE-SPECIFIC — AUTHORITATIVE has "
        "priority over all generic documentation.\n"
        "- Evidence labelled GENERIC CIVIC — SUPPLEMENTARY ONLY may "
        "be used for general procedures, warnings, maintenance methods, "
        "and background information.\n"
        "- Never use a generic Civic numerical specification as though "
        "it were a Type R-specific specification unless the same value "
        "is confirmed by vehicle-specific evidence.\n"
        "- Numerical specifications include tyre sizes, tyre pressures, "
        "wheel sizes, capacities, dimensions, weights, torque values, "
        "performance figures, and other model-dependent measurements.\n"
        "- If vehicle-specific evidence does not provide the requested "
        "number, say that the supplied reference library does not verify "
        "that value for the selected vehicle.\n"
        "- In that situation, do not fill the gap from general model "
        "knowledge. Direct the user to the vehicle placard, official "
        "model-specific documentation, or a qualified professional as "
        "appropriate.\n"
        "- When vehicle-specific and generic evidence conflict, always "
        "follow the vehicle-specific evidence and explain the conflict "
        "briefly if it matters to the answer.\n"
        "- Never claim that Honda documentation says something that is "
        "not present in the supplied reference material.\n"
        "- When you rely on reference material, mention the source name "
        "and page number where practical.\n"
        "- Do not expose similarity scores, retrieval ranking, or other "
        "internal RAG details to the user.\n\n"

        "IMPORTANT FOR MODIFIED VEHICLES:\n"
        "- The selected vehicle description may contain aftermarket "
        "modifications. Do not assume those modifications change an "
        "OEM specification unless the available information proves it.\n"
        "- Distinguish clearly between the vehicle's documented OEM "
        "specification and any advice relating to aftermarket parts."
    )

    request = {
        "model": "gpt-4.1-mini",
        "instructions": instructions,
        "input": user_message,
    }

    if previous_response_id is not None:
        request["previous_response_id"] = (
            previous_response_id
        )

    return client.responses.create(
        **request
    )
