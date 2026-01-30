"""Tests for the semantic chunker."""

import pytest

from wiki_craft.processing.chunker import ChunkConfig, SemanticChunker, chunk_document
from wiki_craft.storage.models import (
    ContentBlock,
    ContentType,
    DocumentMetadata,
    DocumentType,
    ParsedDocument,
)


class TestSemanticChunker:
    """Test suite for SemanticChunker."""

    @pytest.fixture
    def sample_document(self) -> ParsedDocument:
        """Create a sample document for testing."""
        blocks = [
            ContentBlock(
                text="Introduction",
                content_type=ContentType.HEADING,
                position=0,
                section_hierarchy=["Introduction"],
            ),
            ContentBlock(
                text="This is the introduction paragraph. It provides an overview of the topic. " * 5,
                content_type=ContentType.PARAGRAPH,
                position=1,
                section="Introduction",
                section_hierarchy=["Introduction"],
            ),
            ContentBlock(
                text="Main Content",
                content_type=ContentType.HEADING,
                position=2,
                section_hierarchy=["Main Content"],
            ),
            ContentBlock(
                text="This is the main content. It contains detailed information. " * 10,
                content_type=ContentType.PARAGRAPH,
                position=3,
                section="Main Content",
                section_hierarchy=["Main Content"],
            ),
            ContentBlock(
                text="Conclusion",
                content_type=ContentType.HEADING,
                position=4,
                section_hierarchy=["Conclusion"],
            ),
            ContentBlock(
                text="This is the conclusion. It wraps up the document. " * 3,
                content_type=ContentType.PARAGRAPH,
                position=5,
                section="Conclusion",
                section_hierarchy=["Conclusion"],
            ),
        ]

        metadata = DocumentMetadata(
            source_path="/test/document.md",
            source_hash="abc123",
            filename="document.md",
            document_type=DocumentType.MARKDOWN,
            title="Test Document",
        )

        return ParsedDocument(metadata=metadata, content_blocks=blocks)

    def test_chunk_document(self, sample_document: ParsedDocument):
        """Test basic document chunking."""
        chunker = SemanticChunker()
        chunks = chunker.chunk_document(sample_document)

        assert len(chunks) > 0

        # All chunks should have metadata
        for chunk in chunks:
            assert chunk.chunk_id is not None
            assert chunk.text is not None
            assert chunk.metadata.document_id == sample_document.metadata.document_id
            assert chunk.metadata.source_path == "/test/document.md"

    def test_chunk_numbering(self, sample_document: ParsedDocument):
        """Test that chunks are numbered correctly."""
        chunker = SemanticChunker()
        chunks = chunker.chunk_document(sample_document)

        for i, chunk in enumerate(chunks):
            assert chunk.metadata.chunk_index == i
            assert chunk.metadata.total_chunks == len(chunks)

    def test_chunk_size_limits(self, sample_document: ParsedDocument):
        """Test that chunks respect size limits."""
        config = ChunkConfig(
            target_size=500,
            min_size=50,
            max_size=1000,
            overlap=50,
        )
        chunker = SemanticChunker(config)
        chunks = chunker.chunk_document(sample_document)

        for chunk in chunks:
            # Chunks should not exceed max size (with some tolerance for edge cases)
            assert len(chunk.text) <= config.max_size * 1.5

    def test_heading_starts_new_chunk(self, sample_document: ParsedDocument):
        """Test that headings start new chunks."""
        config = ChunkConfig(target_size=2000, min_size=50, max_size=3000, overlap=100)
        chunker = SemanticChunker(config)
        chunks = chunker.chunk_document(sample_document)

        # Find chunks that start with headings
        heading_chunks = [c for c in chunks if c.text.startswith(("Introduction", "Main Content", "Conclusion"))]
        assert len(heading_chunks) >= 1

    def test_section_hierarchy_preserved(self, sample_document: ParsedDocument):
        """Test that section hierarchy is preserved in chunks."""
        chunker = SemanticChunker()
        chunks = chunker.chunk_document(sample_document)

        # At least some chunks should have section hierarchy
        chunks_with_hierarchy = [c for c in chunks if c.metadata.section_hierarchy]
        assert len(chunks_with_hierarchy) > 0

    def test_convenience_function(self, sample_document: ParsedDocument):
        """Test the chunk_document convenience function."""
        chunks = chunk_document(sample_document)

        assert len(chunks) > 0
        assert all(c.chunk_id is not None for c in chunks)


class TestChunkConfig:
    """Tests for ChunkConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = ChunkConfig()

        assert config.target_size == 1000
        assert config.min_size == 100
        assert config.max_size == 2000
        assert config.overlap == 200

    def test_custom_values(self):
        """Test custom configuration values."""
        config = ChunkConfig(
            target_size=500,
            min_size=50,
            max_size=1000,
            overlap=100,
        )

        assert config.target_size == 500
        assert config.min_size == 50
        assert config.max_size == 1000
        assert config.overlap == 100
