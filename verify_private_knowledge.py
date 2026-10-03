from garage_ai import get_reference_context
from rag import retrieve_knowledge


EP3_SCOPE = "civic_type_r_ep3"

CHECKS = [
    {
        "name": "EP3 tyre specification",
        "question": (
            "What tyre size does the 2004 Honda Civic Type R EP3 use?"
        ),
        "require_vehicle_specific": True,
    },
    {
        "name": "EP3 tyre pressure grounding",
        "question": (
            "What tyre pressure should I use on a 2004 Honda Civic Type R EP3?"
        ),
        "require_vehicle_specific": True,
    },
]


def run_check(check: dict) -> None:
    """Run one live retrieval verification against the secured index."""

    print()
    print(
        f"CHECK: {check['name']}"
    )
    print(
        f"Question: {check['question']}"
    )

    chunks = retrieve_knowledge(
        check["question"],
        match_count=5,
        vehicle_scope=EP3_SCOPE,
    )

    if not chunks:
        raise RuntimeError(
            f"{check['name']}: no knowledge chunks were returned."
        )

    if check["require_vehicle_specific"]:
        if not any(
            chunk.get("evidence_level")
            == "vehicle_specific"
            for chunk in chunks
        ):
            raise RuntimeError(
                f"{check['name']}: no vehicle-specific evidence was returned."
            )

    print(
        f"Retrieved {len(chunks)} distinct chunks:"
    )

    for index, chunk in enumerate(
        chunks,
        start=1,
    ):
        print(
            f"  {index}. "
            f"{chunk.get('source_name')} "
            f"page {chunk.get('page_number')} "
            f"[{chunk.get('evidence_level')}]"
        )


def main() -> None:
    print(
        "VCG M11 private knowledge verification"
    )
    print(
        "-------------------------------------"
    )

    for check in CHECKS:
        run_check(
            check
        )

    print()
    print(
        "REFERENCE CONTEXT PREVIEW"
    )

    context = get_reference_context(
        (
            "What tyre size does the 2004 Honda Civic "
            "Type R EP3 use?"
        ),
        (
            "2004 Honda Civic Type R EP3, "
            "2.0 K20 engine"
        ),
    )

    if (
        "VEHICLE-SPECIFIC — AUTHORITATIVE"
        not in context
    ):
        raise RuntimeError(
            "Garage AI context did not preserve the "
            "vehicle-specific authority label."
        )

    print(
        context[:1800]
    )

    print()
    print(
        "M11 knowledge retrieval verification PASSED."
    )


if __name__ == "__main__":
    main()
