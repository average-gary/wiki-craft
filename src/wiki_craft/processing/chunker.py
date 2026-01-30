"""
Semantic chunking for document content.

Splits documents into meaningful chunks while preserving context
and section hierarchy for accurate source attribution.
"""

import logging
import re
from dataclasses import dataclass

from wiki_craft.config import settings
from wiki_craft.storage.models import (
    ChunkMetadata,
    ContentBlock,
    ContentType,
    DocumentMetadata,
    ParsedDocument,
    StoredChunk,
)

logger = logging.getLogger(__name__)


@dataclass
class ChunkConfig:
    """Configuration for chunking behavior."""

    target_size: int = 1000  # Target chunk size in characters
    min_size: int = 100  # Minimum chunk size
    max_size: int = 2000  # Maximum chunk size
    overlap: int = 200  # Overlap between chunks


class SemanticChunker:
    """
    Splits documents into semantic chunks for embedding.

    Preserves document structure by:
    - Keeping headings with their content
    - Not splitting mid-sentence when possible
    - Maintaining section hierarchy in metadata
    - Adding overlap between chunks for continuity
    """

    def __init__(self, config: ChunkConfig | None = None) -> None:
        """Initialize the chunker with optional configuration."""
        self.config = config or ChunkConfig(
            target_size=settings.chunk_size,
            min_size=settings.min_chunk_size,
            max_size=settings.max_chunk_size,
            overlap=settings.chunk_overlap,
        )

    def chunk_document(self, document: ParsedDocument) -> list[StoredChunk]:
        """
        Split a parsed document into chunks with metadata.

        Args:
            document: Parsed document with content blocks

        Returns:
            List of StoredChunk objects ready for embedding
        """
        chunks: list[StoredChunk] = []
        current_text = ""
        current_blocks: list[ContentBlock] = []
        char_offset = 0

        for block in document.content_blocks:
            # Headings start new chunks (unless very short)
            if block.content_type == ContentType.HEADING:
                # Save current chunk if substantial
                if len(current_text.strip()) >= self.config.min_size:
                    chunks.extend(
                        self._create_chunks(
                            current_text, current_blocks, document.metadata, char_offset
                        )
                    )
                    char_offset += len(current_text)

                # Start new chunk with heading
                current_text = block.text + "\n\n"
                current_blocks = [block]
                continue

            # Add block to current chunk
            block_text = block.text.strip()
            if not block_text:
                continue

            potential_text = current_text + block_text + "\n\n"

            # If adding this block exceeds max size, split
            if len(potential_text) > self.config.max_size:
                # Save current chunk
                if len(current_text.strip()) >= self.config.min_size:
                    chunks.extend(
                        self._create_chunks(
                            current_text, current_blocks, document.metadata, char_offset
                        )
                    )
                    char_offset += len(current_text)

                # Handle large blocks that need splitting
                if len(block_text) > self.config.max_size:
                    split_chunks = self._split_large_block(block, document.metadata, char_offset)
                    chunks.extend(split_chunks)
                    char_offset += len(block_text)
                    current_text = ""
                    current_blocks = []
                else:
                    # Start new chunk with this block
                    current_text = block_text + "\n\n"
                    current_blocks = [block]
            else:
                current_text = potential_text
                current_blocks.append(block)

        # Don't forget the last chunk
        if len(current_text.strip()) >= self.config.min_size:
            chunks.extend(
                self._create_chunks(current_text, current_blocks, document.metadata, char_offset)
            )

        # Number chunks
        total_chunks = len(chunks)
        for i, chunk in enumerate(chunks):
            chunk.metadata.chunk_index = i
            chunk.metadata.total_chunks = total_chunks

        logger.info(f"Created {len(chunks)} chunks from document {document.metadata.document_id}")
        return chunks

    def _create_chunks(
        self,
        text: str,
        blocks: list[ContentBlock],
        doc_meta: DocumentMetadata,
        char_offset: int,
    ) -> list[StoredChunk]:
        """
        Create chunk(s) from accumulated text and blocks.

        Handles splitting if text exceeds target size.
        """
        text = text.strip()
        if not text:
            return []

        # If within target size, create single chunk
        if len(text) <= self.config.target_size:
            return [self._make_chunk(text, blocks, doc_meta, char_offset)]

        # Split into multiple chunks with overlap
        chunks = []
        sentences = self._split_sentences(text)
        current_chunk_text = ""
        current_chunk_blocks = []
        chunk_start = char_offset

        for sentence in sentences:
            if len(current_chunk_text) + len(sentence) > self.config.target_size:
                if current_chunk_text:
                    # Find relevant blocks for this chunk
                    relevant_blocks = self._find_relevant_blocks(
                        current_chunk_text, blocks, text, chunk_start - char_offset
                    )
                    chunks.append(
                        self._make_chunk(
                            current_chunk_text.strip(), relevant_blocks, doc_meta, chunk_start
                        )
                    )

                    # Add overlap
                    overlap_text = self._get_overlap(current_chunk_text)
                    chunk_start += len(current_chunk_text) - len(overlap_text)
                    current_chunk_text = overlap_text + sentence
                else:
                    current_chunk_text = sentence
            else:
                current_chunk_text += sentence

        # Last chunk
        if current_chunk_text.strip():
            relevant_blocks = self._find_relevant_blocks(
                current_chunk_text, blocks, text, chunk_start - char_offset
            )
            chunks.append(
                self._make_chunk(current_chunk_text.strip(), relevant_blocks, doc_meta, chunk_start)
            )

        return chunks

    def _split_large_block(
        self, block: ContentBlock, doc_meta: DocumentMetadata, char_offset: int
    ) -> list[StoredChunk]:
        """Split a single large block into multiple chunks."""
        text = block.text.strip()
        sentences = self._split_sentences(text)

        chunks = []
        current_text = ""
        current_start = char_offset

        for sentence in sentences:
            if len(current_text) + len(sentence) > self.config.target_size:
                if current_text:
                    chunks.append(
                        self._make_chunk(current_text.strip(), [block], doc_meta, current_start)
                    )
                    overlap = self._get_overlap(current_text)
                    current_start += len(current_text) - len(overlap)
                    current_text = overlap + sentence
                else:
                    # Single sentence exceeds max, force split
                    current_text = sentence[: self.config.max_size]
            else:
                current_text += sentence

        if current_text.strip():
            chunks.append(self._make_chunk(current_text.strip(), [block], doc_meta, current_start))

        return chunks

    def _make_chunk(
        self,
        text: str,
        blocks: list[ContentBlock],
        doc_meta: DocumentMetadata,
        char_offset: int,
    ) -> StoredChunk:
        """Create a StoredChunk with full metadata."""
        # Get metadata from first block (primary source)
        first_block = blocks[0] if blocks else None

        metadata = ChunkMetadata(
            document_id=doc_meta.document_id,
            source_path=doc_meta.source_path,
            source_hash=doc_meta.source_hash,
            document_title=doc_meta.title,
            document_type=doc_meta.document_type,
            page_number=first_block.page_number if first_block else None,
            section_hierarchy=first_block.section_hierarchy if first_block else [],
            paragraph_index=first_block.position if first_block else 0,
            chunk_index=0,  # Will be set later
            total_chunks=0,  # Will be set later
            content_type=first_block.content_type if first_block else ContentType.PARAGRAPH,
            char_start=char_offset,
            char_end=char_offset + len(text),
            document_version=doc_meta.version,
        )

        return StoredChunk(text=text, metadata=metadata)

    def _split_sentences(self, text: str) -> list[str]:
        """
        Split text into sentences, keeping punctuation attached.

        Uses regex to handle common sentence boundaries while
        avoiding splits on abbreviations and decimals.
        """
        # Pattern matches sentence endings
        pattern = r"(?<=[.!?])\s+(?=[A-Z])"
        sentences = re.split(pattern, text)

        # Ensure each "sentence" ends with space for rejoining
        return [s + " " for s in sentences]

    def _get_overlap(self, text: str) -> str:
        """Get the overlap portion from the end of text."""
        if len(text) <= self.config.overlap:
            return text

        # Try to break at sentence boundary
        overlap_region = text[-self.config.overlap * 2 :]
        sentences = self._split_sentences(overlap_region)

        if len(sentences) > 1:
            # Return last sentence(s) up to overlap size
            result = ""
            for s in reversed(sentences):
                if len(result) + len(s) <= self.config.overlap:
                    result = s + result
                else:
                    break
            return result if result else text[-self.config.overlap :]

        return text[-self.config.overlap :]

    def _find_relevant_blocks(
        self, chunk_text: str, blocks: list[ContentBlock], full_text: str, offset: int
    ) -> list[ContentBlock]:
        """Find which blocks contributed to this chunk."""
        relevant = []
        for block in blocks:
            # Check if block text appears in chunk
            if block.text[:50] in chunk_text or block.text[-50:] in chunk_text:
                relevant.append(block)
        return relevant if relevant else blocks[:1]


def chunk_document(document: ParsedDocument) -> list[StoredChunk]:
    """
    Convenience function to chunk a document with default settings.

    Args:
        document: Parsed document to chunk

    Returns:
        List of StoredChunk objects
    """
    chunker = SemanticChunker()
    return chunker.chunk_document(document)
