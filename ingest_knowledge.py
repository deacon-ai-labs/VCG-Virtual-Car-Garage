import argparse
from pathlib import Path

import pymupdf
from openai import OpenAI

from knowledge_admin import (
    get_knowledge_admin_client,
)
from knowledge_config import DOCUMENTS


DEFAULT_SOURCE_DIR = Path("private_knowledge")

CHUNK_SIZE = 1400
CHUNK_OVERLAP = 200

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_BATCH_SIZE = 50
DATABASE_BATCH_SIZE = 100


def split_text(text: str) -> list[str]:
    """Split text into overlapping chunks."""

    text = " ".join(text.split())

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = start + CHUNK_SIZE
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = end - CHUNK_OVERLAP

    return chunks


def validate_source_files(
    source_dir: Path,
) -> None:
    """Fail before any database change if a configured source is missing."""

    missing = [
        filename
        for filename in DOCUMENTS
        if not (
            source_dir / filename
        ).is_file()
    ]

    if missing:
        raise FileNotFoundError(
            "Missing private knowledge files in "
            f"{source_dir}: "
            + ", ".join(missing)
        )


def extract_chunks(
    source_dir: Path,
) -> list[dict]:
    """Extract page-aware chunks from admin-only local PDF sources."""

    validate_source_files(
        source_dir
    )

    chunks = []

    for filename, metadata in DOCUMENTS.items():
        pdf_path = (
            source_dir / filename
        )

        print()
        print(
            f"Reading private source {filename}..."
        )

        document = pymupdf.open(
            str(pdf_path)
        )

        try:
            document_chunk_count = 0

            for page_index, page in enumerate(
                document
            ):
                page_text = (
                    page.get_text("text")
                    or ""
                )

                for chunk in split_text(
                    page_text
                ):
                    chunks.append(
                        {
                            "source_name": (
                                metadata[
                                    "source_name"
                                ]
                            ),
                            "source_type": (
                                metadata[
                                    "source_type"
                                ]
                            ),
                            "vehicle_scope": (
                                metadata[
                                    "vehicle_scope"
                                ]
                            ),
                            "page_number": (
                                page_index + 1
                            ),
                            "content": chunk,
                        }
                    )

                    document_chunk_count += 1

            print(
                f"Finished {filename}: "
                f"{len(document)} pages, "
                f"{document_chunk_count} chunks"
            )

        finally:
            document.close()

    return chunks


def add_embeddings(
    chunks: list[dict],
) -> list[dict]:
    """Create an embedding for every knowledge chunk."""

    client = OpenAI()
    total = len(chunks)

    for start in range(
        0,
        total,
        EMBEDDING_BATCH_SIZE,
    ):
        batch = chunks[
            start:start + EMBEDDING_BATCH_SIZE
        ]

        response = (
            client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=[
                    chunk["content"]
                    for chunk in batch
                ],
            )
        )

        for chunk, result in zip(
            batch,
            response.data,
        ):
            chunk["embedding"] = (
                result.embedding
            )

        completed = min(
            start + EMBEDDING_BATCH_SIZE,
            total,
        )

        print(
            f"Created embeddings: "
            f"{completed}/{total}"
        )

    return chunks


def validate_source_types(
    chunks: list[dict],
) -> None:
    """Confirm every expected source category was extracted."""

    source_types = {
        chunk["source_type"]
        for chunk in chunks
    }

    expected_source_types = {
        metadata["source_type"]
        for metadata in DOCUMENTS.values()
    }

    missing = (
        expected_source_types
        - source_types
    )

    if missing:
        raise RuntimeError(
            "Missing extracted source types: "
            + ", ".join(
                sorted(missing)
            )
        )


def clear_existing_documents(
    client,
) -> None:
    """Remove old vector chunks for configured sources."""

    for metadata in DOCUMENTS.values():
        (
            client.table(
                "knowledge_chunks"
            )
            .delete()
            .eq(
                "source_name",
                metadata["source_name"],
            )
            .execute()
        )


def save_chunks(
    client,
    chunks: list[dict],
) -> None:
    """Insert knowledge chunks into Supabase."""

    total = len(chunks)

    for start in range(
        0,
        total,
        DATABASE_BATCH_SIZE,
    ):
        batch = chunks[
            start:start + DATABASE_BATCH_SIZE
        ]

        (
            client.table(
                "knowledge_chunks"
            )
            .insert(
                batch
            )
            .execute()
        )

        completed = min(
            start + DATABASE_BATCH_SIZE,
            total,
        )

        print(
            f"Saved to Supabase: "
            f"{completed}/{total}"
        )


def ingest(
    source_dir: Path,
) -> None:
    """
    Build the private knowledge index from admin-only local sources.

    Existing working RAG rows are left untouched until every PDF has been
    read successfully and every new chunk has received an embedding.
    """

    source_dir = (
        source_dir
        .expanduser()
        .resolve()
    )

    print(
        "Virtual Car Garage private knowledge ingestion"
    )
    print(
        "--------------------------------------------"
    )
    print(
        f"Source directory: {source_dir}"
    )

    chunks = extract_chunks(
        source_dir
    )

    print()
    print(
        f"Created {len(chunks)} text chunks."
    )

    if not chunks:
        raise RuntimeError(
            "No knowledge chunks were extracted."
        )

    validate_source_types(
        chunks
    )

    print()
    print(
        "Creating OpenAI embeddings..."
    )

    chunks = add_embeddings(
        chunks
    )

    admin_client = (
        get_knowledge_admin_client()
    )

    print()
    print(
        "Replacing indexed knowledge..."
    )

    clear_existing_documents(
        admin_client
    )

    save_chunks(
        admin_client,
        chunks,
    )

    print()
    print(
        "Knowledge ingestion complete."
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Build the VCG RAG index from private local PDF sources."
        )
    )

    parser.add_argument(
        "--source-dir",
        default=str(
            DEFAULT_SOURCE_DIR
        ),
        help=(
            "Admin-only directory containing the configured PDFs. "
            "Defaults to ./private_knowledge."
        ),
    )

    args = parser.parse_args()

    ingest(
        Path(args.source_dir)
    )


if __name__ == "__main__":
    main()
