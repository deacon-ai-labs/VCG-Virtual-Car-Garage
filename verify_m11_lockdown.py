from database import get_supabase_client
from rag import (
    create_query_embedding,
    retrieve_knowledge,
)


EP3_SCOPE = "civic_type_r_ep3"
TEST_QUESTION = (
    "What tyre size does the 2004 Honda Civic Type R EP3 use?"
)


def expect_public_table_blocked() -> None:
    """Confirm the ordinary publishable client cannot read RAG rows."""

    public_client = get_supabase_client()

    try:
        (
            public_client.table(
                "knowledge_chunks"
            )
            .select(
                "source_name"
            )
            .limit(
                1
            )
            .execute()
        )
    except Exception:
        print(
            "PASS: publishable client cannot read knowledge_chunks."
        )
        return

    raise RuntimeError(
        "SECURITY FAILURE: publishable client can still "
        "read knowledge_chunks."
    )


def expect_public_rpc_blocked() -> None:
    """Confirm the ordinary publishable client cannot execute RAG search."""

    public_client = get_supabase_client()

    query_embedding = (
        create_query_embedding(
            TEST_QUESTION
        )
    )

    try:
        (
            public_client.rpc(
                "match_knowledge_chunks",
                {
                    "query_embedding": query_embedding,
                    "match_count": 1,
                    "filter_vehicle_scope": EP3_SCOPE,
                },
            )
            .execute()
        )
    except Exception:
        print(
            "PASS: publishable client cannot execute "
            "match_knowledge_chunks."
        )
        return

    raise RuntimeError(
        "SECURITY FAILURE: publishable client can still "
        "execute match_knowledge_chunks."
    )


def expect_server_rag_works() -> None:
    """Confirm Garage AI's server-only retrieval path still works."""

    chunks = retrieve_knowledge(
        TEST_QUESTION,
        match_count=5,
        vehicle_scope=EP3_SCOPE,
    )

    if not chunks:
        raise RuntimeError(
            "RUNTIME FAILURE: server RAG returned no knowledge."
        )

    if not any(
        chunk.get("evidence_level")
        == "vehicle_specific"
        for chunk in chunks
    ):
        raise RuntimeError(
            "RUNTIME FAILURE: no EP3-specific evidence "
            "was returned."
        )

    print(
        "PASS: server-only RAG still returns "
        "EP3-specific evidence."
    )


def main() -> None:
    print(
        "VCG M11 security lockdown verification"
    )
    print(
        "--------------------------------------"
    )

    expect_public_table_blocked()
    expect_public_rpc_blocked()
    expect_server_rag_works()

    print()
    print(
        "M11 SECURITY LOCKDOWN VERIFIED."
    )


if __name__ == "__main__":
    main()
