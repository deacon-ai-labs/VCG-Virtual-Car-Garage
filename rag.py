from difflib import SequenceMatcher

from openai import OpenAI

from database import get_supabase_client


EMBEDDING_MODEL = "text-embedding-3-small"

DEFAULT_MATCH_COUNT = 5
DEFAULT_CANDIDATE_COUNT = 10

GENERIC_CIVIC_SCOPE = "civic_3door_all_models"

VEHICLE_SPECIFIC_COUNT = 3
DUPLICATE_THRESHOLD = 0.90


def create_query_embedding(question: str) -> list[float]:
    """Create an embedding for a user question."""

    client = OpenAI()

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=question,
    )

    return response.data[0].embedding


def search_knowledge_chunks(
    query_embedding: list[float],
    match_count: int,
    vehicle_scope: str | None,
) -> list[dict]:
    """Search Supabase for semantically similar knowledge chunks."""

    supabase = get_supabase_client()

    response = (
        supabase.rpc(
            "match_knowledge_chunks",
            {
                "query_embedding": query_embedding,
                "match_count": match_count,
                "filter_vehicle_scope": vehicle_scope,
            },
        )
        .execute()
    )

    return response.data or []


def _normalise_text(text: str) -> str:
    """Normalise text before comparing chunks for duplication."""

    return " ".join(text.lower().split())


def _is_near_duplicate(
    candidate: dict,
    selected: list[dict],
) -> bool:
    """Return True if a chunk is already represented in selected results."""

    candidate_text = _normalise_text(
        candidate.get("content", "")
    )

    if not candidate_text:
        return True

    for existing in selected:
        existing_text = _normalise_text(
            existing.get("content", "")
        )

        if not existing_text:
            continue

        if candidate_text == existing_text:
            return True

        ratio = SequenceMatcher(
            None,
            candidate_text,
            existing_text,
            autojunk=False,
        ).ratio()

        if ratio >= DUPLICATE_THRESHOLD:
            return True

    return False


def _label_chunks(
    chunks: list[dict],
    evidence_level: str,
) -> list[dict]:
    """Add an evidence-authority label to retrieved chunks."""

    labelled = []

    for chunk in chunks:
        item = dict(chunk)
        item["evidence_level"] = evidence_level
        labelled.append(item)

    return labelled


def _take_distinct(
    candidates: list[dict],
    selected: list[dict],
    count: int,
) -> list[dict]:
    """Take up to count distinct chunks, avoiding duplicates."""

    added = []

    for candidate in candidates:
        comparison_pool = selected + added

        if _is_near_duplicate(
            candidate,
            comparison_pool,
        ):
            continue

        added.append(candidate)

        if len(added) >= count:
            break

    return added


def retrieve_knowledge(
    question: str,
    match_count: int = DEFAULT_MATCH_COUNT,
    vehicle_scope: str | None = None,
    candidate_count: int = DEFAULT_CANDIDATE_COUNT,
) -> list[dict]:
    """
    Return relevant, distinct knowledge chunks.

    For a known vehicle scope, vehicle-specific evidence is returned first
    and treated as authoritative. Generic Civic material is supplementary
    and is included only to help with general procedures or maintenance.
    """

    question = question.strip()

    if not question:
        raise ValueError(
            "Question must not be empty."
        )

    if match_count < 1:
        raise ValueError(
            "match_count must be at least 1."
        )

    candidate_count = max(
        candidate_count,
        match_count,
    )

    query_embedding = (
        create_query_embedding(question)
    )

    if not vehicle_scope:
        candidates = search_knowledge_chunks(
            query_embedding,
            candidate_count,
            None,
        )

        candidates = _label_chunks(
            candidates,
            "unscoped",
        )

        return _take_distinct(
            candidates,
            selected=[],
            count=match_count,
        )

    specific_candidates = search_knowledge_chunks(
        query_embedding,
        candidate_count,
        vehicle_scope,
    )

    specific_candidates = _label_chunks(
        specific_candidates,
        "vehicle_specific",
    )

    specific_target = min(
        VEHICLE_SPECIFIC_COUNT,
        match_count,
    )

    selected = _take_distinct(
        specific_candidates,
        selected=[],
        count=specific_target,
    )

    remaining = match_count - len(selected)

    if (
        remaining > 0
        and vehicle_scope != GENERIC_CIVIC_SCOPE
    ):
        generic_candidates = search_knowledge_chunks(
            query_embedding,
            candidate_count,
            GENERIC_CIVIC_SCOPE,
        )

        generic_candidates = _label_chunks(
            generic_candidates,
            "generic_supplementary",
        )

        selected.extend(
            _take_distinct(
                generic_candidates,
                selected=selected,
                count=remaining,
            )
        )

    remaining = match_count - len(selected)

    if remaining > 0:
        selected.extend(
            _take_distinct(
                specific_candidates,
                selected=selected,
                count=remaining,
            )
        )

    return selected


def format_knowledge_context(
    chunks: list[dict],
) -> str:
    """Format retrieved evidence for Garage AI."""

    if not chunks:
        return (
            "No relevant reference material "
            "was found."
        )

    sections = []

    for chunk in chunks:
        source_name = chunk.get(
            "source_name",
            "Unknown source",
        )

        page_number = chunk.get(
            "page_number"
        )

        similarity = chunk.get(
            "similarity"
        )

        content = chunk.get(
            "content",
            "",
        )

        evidence_level = chunk.get(
            "evidence_level",
            "unscoped",
        )

        if evidence_level == "vehicle_specific":
            authority_label = (
                "VEHICLE-SPECIFIC — AUTHORITATIVE"
            )
        elif evidence_level == "generic_supplementary":
            authority_label = (
                "GENERIC CIVIC — SUPPLEMENTARY ONLY"
            )
        else:
            authority_label = (
                "REFERENCE MATERIAL"
            )

        source_label = source_name

        if page_number is not None:
            source_label += (
                f", page {page_number}"
            )

        if similarity is not None:
            source_label += (
                f" (similarity "
                f"{float(similarity):.3f})"
            )

        sections.append(
            f"[{authority_label}]\n"
            f"[Source: {source_label}]\n"
            f"{content}"
        )

    return "\n\n".join(sections)


def main() -> None:
    """Run a simple command-line retrieval test."""

    question = input(
        "Ask a Honda knowledge question: "
    ).strip()

    vehicle_scope = input(
        "Vehicle scope "
        "(Enter for all, or civic_type_r_ep3): "
    ).strip()

    if not vehicle_scope:
        vehicle_scope = None

    matches = retrieve_knowledge(
        question,
        vehicle_scope=vehicle_scope,
    )

    print(
        f"\nFound {len(matches)} "
        "distinct matching chunks:\n"
    )

    for index, match in enumerate(
        matches,
        start=1,
    ):
        similarity = float(
            match.get("similarity") or 0.0
        )

        evidence_level = match.get(
            "evidence_level",
            "unscoped",
        )

        print(
            f"{index}. "
            f"{match.get('source_name')} "
            f"(page "
            f"{match.get('page_number')}, "
            f"similarity "
            f"{similarity:.3f}, "
            f"{evidence_level})"
        )

        print(
            match.get(
                "content",
                "",
            )
        )

        print()


if __name__ == "__main__":
    main()
