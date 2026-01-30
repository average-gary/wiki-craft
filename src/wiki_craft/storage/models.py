"""
Data models for Wiki-Craft.

Defines the core data structures used throughout the application for
document parsing, storage, search, and wiki generation.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class ContentType(str, Enum):
    """Types of content blocks extracted from documents."""

    PARAGRAPH = "paragraph"
    HEADING = "heading"
    LIST = "list"
    TABLE = "table"
    CODE = "code"
    QUOTE = "quote"
    IMAGE_CAPTION = "image_caption"
    FOOTNOTE = "footnote"
    UNKNOWN = "unknown"


class DocumentType(str, Enum):
    """Supported document types."""

    PDF = "pdf"
    WORD = "docx"
    EXCEL = "xlsx"
    MARKDOWN = "markdown"
    TEXT = "text"
    HTML = "html"
    EPUB = "epub"
    UNKNOWN = "unknown"


# ============================================================================
# Document Parsing Models
# ============================================================================


class ContentBlock(BaseModel):
    """
    A single block of content extracted from a document.

    Represents a semantic unit like a paragraph, heading, list, or table.
    """

    text: str = Field(..., description="The extracted text content")
    content_type: ContentType = Field(
        default=ContentType.PARAGRAPH, description="Type of content block"
    )
    page_number: int | None = Field(default=None, description="Page number (1-indexed)")
    section: str | None = Field(default=None, description="Section/chapter name")
    section_hierarchy: list[str] = Field(
        default_factory=list, description="Full section path, e.g. ['Chapter 1', '1.2 Overview']"
    )
    position: int = Field(default=0, description="Order within the document")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional parser-specific metadata"
    )


class DocumentMetadata(BaseModel):
    """
    Metadata about a source document.

    Captures information for provenance tracking and deduplication.
    """

    document_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier")
    source_path: str = Field(..., description="Original file path or URL")
    source_hash: str = Field(..., description="SHA-256 hash of file content for deduplication")
    filename: str = Field(..., description="Original filename")
    document_type: DocumentType = Field(..., description="Type of document")
    title: str | None = Field(default=None, description="Document title if available")
    author: str | None = Field(default=None, description="Document author if available")
    created_at: datetime | None = Field(default=None, description="Document creation date")
    modified_at: datetime | None = Field(default=None, description="Document modification date")
    ingested_at: datetime = Field(
        default_factory=datetime.utcnow, description="When document was ingested"
    )
    page_count: int | None = Field(default=None, description="Total pages (for PDFs)")
    word_count: int | None = Field(default=None, description="Approximate word count")
    language: str | None = Field(default=None, description="Detected language")
    version: str | None = Field(default=None, description="Document version if available")
    custom_metadata: dict[str, Any] = Field(
        default_factory=dict, description="User-provided metadata"
    )


class ParsedDocument(BaseModel):
    """
    Result of parsing a document.

    Contains the extracted content blocks and document metadata.
    """

    metadata: DocumentMetadata
    content_blocks: list[ContentBlock] = Field(
        default_factory=list, description="Extracted content blocks"
    )
    raw_text: str | None = Field(default=None, description="Full raw text if available")
    parsing_errors: list[str] = Field(
        default_factory=list, description="Non-fatal errors during parsing"
    )


# ============================================================================
# Chunk Storage Models
# ============================================================================


class ChunkMetadata(BaseModel):
    """
    Full provenance metadata for a stored chunk.

    Enables precise source attribution for any piece of content.
    """

    # Document reference
    document_id: str = Field(..., description="Parent document ID")
    source_path: str = Field(..., description="Original file path")
    source_hash: str = Field(..., description="Document hash for verification")
    document_title: str | None = Field(default=None, description="Document title")
    document_type: DocumentType = Field(..., description="Type of source document")

    # Position within document
    page_number: int | None = Field(default=None, description="Page number (1-indexed)")
    section_hierarchy: list[str] = Field(
        default_factory=list, description="Section path for navigation"
    )
    paragraph_index: int = Field(default=0, description="Paragraph index within section")
    chunk_index: int = Field(..., description="This chunk's index within the document")
    total_chunks: int = Field(..., description="Total chunks from this document")

    # Content info
    content_type: ContentType = Field(default=ContentType.PARAGRAPH)
    char_start: int = Field(default=0, description="Character offset in original text")
    char_end: int = Field(default=0, description="End character offset")

    # Timestamps
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    document_version: str | None = Field(default=None)

    def to_chroma_metadata(self) -> dict[str, Any]:
        """Convert to ChromaDB-compatible metadata dict."""
        return {
            "document_id": self.document_id,
            "source_path": self.source_path,
            "source_hash": self.source_hash,
            "document_title": self.document_title or "",
            "document_type": self.document_type.value,
            "page_number": self.page_number or -1,
            "section_hierarchy": "|".join(self.section_hierarchy),
            "paragraph_index": self.paragraph_index,
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
            "content_type": self.content_type.value,
            "char_start": self.char_start,
            "char_end": self.char_end,
            "ingested_at": self.ingested_at.isoformat(),
            "document_version": self.document_version or "",
        }

    @classmethod
    def from_chroma_metadata(cls, data: dict[str, Any]) -> "ChunkMetadata":
        """Reconstruct from ChromaDB metadata dict."""
        section_hierarchy = data.get("section_hierarchy", "")
        return cls(
            document_id=data["document_id"],
            source_path=data["source_path"],
            source_hash=data["source_hash"],
            document_title=data.get("document_title") or None,
            document_type=DocumentType(data["document_type"]),
            page_number=data.get("page_number") if data.get("page_number", -1) != -1 else None,
            section_hierarchy=section_hierarchy.split("|") if section_hierarchy else [],
            paragraph_index=data.get("paragraph_index", 0),
            chunk_index=data["chunk_index"],
            total_chunks=data["total_chunks"],
            content_type=ContentType(data.get("content_type", "paragraph")),
            char_start=data.get("char_start", 0),
            char_end=data.get("char_end", 0),
            ingested_at=datetime.fromisoformat(data["ingested_at"]),
            document_version=data.get("document_version") or None,
        )


class StoredChunk(BaseModel):
    """A chunk as stored in the vector database."""

    chunk_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique chunk ID")
    text: str = Field(..., description="The chunk text content")
    metadata: ChunkMetadata = Field(..., description="Full provenance metadata")
    embedding: list[float] | None = Field(default=None, description="Vector embedding")


# ============================================================================
# Search Models
# ============================================================================


class SearchResult(BaseModel):
    """A single search result with relevance score and source info."""

    chunk_id: str = Field(..., description="ID of the matched chunk")
    text: str = Field(..., description="The matched text content")
    score: float = Field(..., description="Relevance score (0-1, higher is better)")
    metadata: ChunkMetadata = Field(..., description="Source metadata for attribution")

    @property
    def citation(self) -> str:
        """Generate a citation string for this result."""
        parts = [self.metadata.document_title or self.metadata.source_path]
        if self.metadata.page_number:
            parts.append(f"p. {self.metadata.page_number}")
        if self.metadata.section_hierarchy:
            parts.append(" > ".join(self.metadata.section_hierarchy))
        return ", ".join(parts)


class SearchQuery(BaseModel):
    """Search request parameters."""

    query: str = Field(..., description="Search query text")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results to return")
    min_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum relevance score")
    document_ids: list[str] | None = Field(default=None, description="Filter by document IDs")
    document_types: list[DocumentType] | None = Field(
        default=None, description="Filter by document types"
    )
    include_embeddings: bool = Field(default=False, description="Include embeddings in response")


class SearchResponse(BaseModel):
    """Search response with results and query info."""

    query: str = Field(..., description="Original query")
    results: list[SearchResult] = Field(default_factory=list)
    total_results: int = Field(default=0)
    search_time_ms: float = Field(default=0.0, description="Search execution time")


# ============================================================================
# Wiki Generation Models
# ============================================================================


class WikiSource(BaseModel):
    """A source reference for wiki content."""

    chunk_id: str = Field(..., description="Source chunk ID")
    document_id: str = Field(..., description="Source document ID")
    document_title: str | None = Field(default=None)
    source_path: str = Field(...)
    page_number: int | None = Field(default=None)
    section: str | None = Field(default=None)
    relevance_score: float = Field(default=0.0)
    excerpt: str = Field(..., description="Relevant excerpt from source")

    def format_citation(self, style: str = "inline") -> str:
        """Format source as a citation."""
        title = self.document_title or self.source_path
        if style == "inline":
            if self.page_number:
                return f"[{title}, p. {self.page_number}]"
            return f"[{title}]"
        elif style == "footnote":
            parts = [title]
            if self.page_number:
                parts.append(f"page {self.page_number}")
            if self.section:
                parts.append(f'section "{self.section}"')
            return ", ".join(parts)
        return title


class WikiSection(BaseModel):
    """A section of wiki content with sources."""

    heading: str = Field(..., description="Section heading")
    content: str = Field(..., description="Section content")
    sources: list[WikiSource] = Field(default_factory=list, description="Sources for this section")
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Confidence score based on source quality"
    )
    subsections: list["WikiSection"] = Field(default_factory=list)


class WikiEntry(BaseModel):
    """A complete wiki entry with full source attribution."""

    entry_id: str = Field(default_factory=lambda: str(uuid4()))
    title: str = Field(..., description="Wiki entry title")
    summary: str = Field(default="", description="Brief summary/introduction")
    sections: list[WikiSection] = Field(default_factory=list)
    all_sources: list[WikiSource] = Field(
        default_factory=list, description="Deduplicated list of all sources"
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    query: str = Field(default="", description="Original query that generated this entry")

    def to_markdown(self) -> str:
        """Export wiki entry as Markdown."""
        lines = [f"# {self.title}", ""]
        if self.summary:
            lines.extend([self.summary, ""])

        for section in self.sections:
            lines.extend(self._section_to_markdown(section, level=2))

        # Add references section
        if self.all_sources:
            lines.extend(["", "## References", ""])
            for i, source in enumerate(self.all_sources, 1):
                lines.append(f"{i}. {source.format_citation('footnote')}")

        return "\n".join(lines)

    def _section_to_markdown(self, section: WikiSection, level: int) -> list[str]:
        """Convert a section to Markdown lines."""
        prefix = "#" * level
        lines = [f"{prefix} {section.heading}", "", section.content, ""]
        for subsection in section.subsections:
            lines.extend(self._section_to_markdown(subsection, level + 1))
        return lines

    def to_html(self) -> str:
        """Export wiki entry as HTML."""
        html_parts = [f"<article>", f"<h1>{self.title}</h1>"]
        if self.summary:
            html_parts.append(f"<p class='summary'>{self.summary}</p>")

        for section in self.sections:
            html_parts.extend(self._section_to_html(section, level=2))

        # References
        if self.all_sources:
            html_parts.append("<section class='references'><h2>References</h2><ol>")
            for source in self.all_sources:
                html_parts.append(f"<li>{source.format_citation('footnote')}</li>")
            html_parts.append("</ol></section>")

        html_parts.append("</article>")
        return "\n".join(html_parts)

    def _section_to_html(self, section: WikiSection, level: int) -> list[str]:
        """Convert a section to HTML."""
        tag = f"h{min(level, 6)}"
        parts = [f"<section>", f"<{tag}>{section.heading}</{tag}>", f"<p>{section.content}</p>"]
        for subsection in section.subsections:
            parts.extend(self._section_to_html(subsection, level + 1))
        parts.append("</section>")
        return parts

    def to_json_dict(self) -> dict[str, Any]:
        """Export wiki entry as a JSON-serializable dict."""
        return self.model_dump(mode="json")


# ============================================================================
# API Request/Response Models
# ============================================================================


class IngestRequest(BaseModel):
    """Request to ingest a document from URL."""

    url: str = Field(..., description="URL to fetch and ingest")
    custom_metadata: dict[str, Any] = Field(default_factory=dict)


class IngestResponse(BaseModel):
    """Response after document ingestion."""

    document_id: str
    filename: str
    document_type: DocumentType
    chunks_created: int
    status: str = "success"
    errors: list[str] = Field(default_factory=list)


class DocumentListResponse(BaseModel):
    """Response listing documents."""

    documents: list[DocumentMetadata]
    total: int
    offset: int
    limit: int


class WikiGenerateRequest(BaseModel):
    """Request to generate a wiki entry."""

    query: str = Field(..., description="Topic or question for wiki entry")
    max_sources: int = Field(default=10, ge=1, le=50)
    output_format: str = Field(default="markdown", pattern="^(markdown|html|json)$")
    include_sources: bool = Field(default=True, description="Include source attributions")


class WikiGenerateResponse(BaseModel):
    """Response with generated wiki content."""

    entry: WikiEntry
    content: str = Field(..., description="Formatted content in requested format")
    format: str
