"""
Wiki-Craft: Document ingestion and indexing system for building wiki-style knowledge bases.

This package provides:
- Multi-format document parsing (PDF, Office, Markdown, HTML, EPUB)
- Semantic chunking with full provenance tracking
- Vector embeddings using sentence-transformers
- ChromaDB storage for semantic search
- REST API for document management and wiki generation
"""

__version__ = "0.1.0"

from wiki_craft.storage.models import (
    ChunkMetadata,
    ContentBlock,
    DocumentMetadata,
    ParsedDocument,
    SearchResult,
    WikiEntry,
)

__all__ = [
    "__version__",
    "ContentBlock",
    "DocumentMetadata",
    "ParsedDocument",
    "ChunkMetadata",
    "SearchResult",
    "WikiEntry",
]
