import tempfile
import unittest
from pathlib import Path

import ingest_knowledge
from knowledge_config import DOCUMENTS


class TestPrivateKnowledgeIngestion(
    unittest.TestCase
):

    def test_split_text_empty(self):
        self.assertEqual(
            ingest_knowledge.split_text(
                "  \n "
            ),
            [],
        )

    def test_validate_source_files_rejects_missing_sources(
        self,
    ):
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(
                temp_dir
            )

            with self.assertRaises(
                FileNotFoundError
            ) as context:
                ingest_knowledge.validate_source_files(
                    source_dir
                )

            message = str(
                context.exception
            )

            for filename in DOCUMENTS:
                self.assertIn(
                    filename,
                    message,
                )

    def test_validate_source_files_accepts_complete_manifest(
        self,
    ):
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(
                temp_dir
            )

            for filename in DOCUMENTS:
                (
                    source_dir
                    / filename
                ).write_bytes(
                    b"test"
                )

            ingest_knowledge.validate_source_files(
                source_dir
            )

    def test_expected_source_types_come_from_manifest(
        self,
    ):
        chunks = [
            {
                "source_type": metadata[
                    "source_type"
                ]
            }
            for metadata in DOCUMENTS.values()
        ]

        ingest_knowledge.validate_source_types(
            chunks
        )


if __name__ == "__main__":
    unittest.main()
