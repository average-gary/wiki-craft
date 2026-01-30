"""
Metadata extraction and enrichment utilities.

Extracts and enhances metadata from documents for better searchability.
"""

import hashlib
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from wiki_craft.storage.models import DocumentMetadata, DocumentType, ParsedDocument

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """
    Extracts and enriches document metadata.

    Capabilities:
    - Detect document type from extension/content
    - Extract title from content if not in metadata
    - Estimate language
    - Generate document fingerprints
    """

    # Common title patterns in documents
    TITLE_PATTERNS = [
        r"^#\s+(.+)$",  # Markdown h1
        r"^(.+)\n={3,}$",  # Setext h1
        r"<title>(.+?)</title>",  # HTML title
        r"^Title:\s*(.+)$",  # Explicit title
    ]

    # Extension to document type mapping
    EXTENSION_MAP = {
        ".pdf": DocumentType.PDF,
        ".docx": DocumentType.WORD,
        ".doc": DocumentType.WORD,
        ".xlsx": DocumentType.EXCEL,
        ".xls": DocumentType.EXCEL,
        ".md": DocumentType.MARKDOWN,
        ".markdown": DocumentType.MARKDOWN,
        ".txt": DocumentType.TEXT,
        ".text": DocumentType.TEXT,
        ".rst": DocumentType.TEXT,
        ".html": DocumentType.HTML,
        ".htm": DocumentType.HTML,
        ".xhtml": DocumentType.HTML,
        ".epub": DocumentType.EPUB,
    }

    def __init__(self) -> None:
        """Initialize the metadata extractor."""
        pass

    def detect_document_type(
        self, file_path: Path, mime_type: str | None = None
    ) -> DocumentType:
        """
        Detect document type from file extension or MIME type.

        Args:
            file_path: Path to the file
            mime_type: Optional MIME type hint

        Returns:
            Detected DocumentType
        """
        # Try extension first
        ext = file_path.suffix.lower()
        if ext in self.EXTENSION_MAP:
            return self.EXTENSION_MAP[ext]

        # Try MIME type
        if mime_type:
            if "pdf" in mime_type:
                return DocumentType.PDF
            elif "word" in mime_type or "docx" in mime_type:
                return DocumentType.WORD
            elif "excel" in mime_type or "spreadsheet" in mime_type:
                return DocumentType.EXCEL
            elif "html" in mime_type:
                return DocumentType.HTML
            elif "epub" in mime_type:
                return DocumentType.EPUB
            elif "markdown" in mime_type:
                return DocumentType.MARKDOWN
            elif "text" in mime_type:
                return DocumentType.TEXT

        return DocumentType.UNKNOWN

    def extract_title(self, text: str, metadata: DocumentMetadata) -> str | None:
        """
        Extract title from document content if not already present.

        Args:
            text: Document text content
            metadata: Existing metadata

        Returns:
            Extracted title or None
        """
        if metadata.title:
            return metadata.title

        # Try each pattern
        for pattern in self.TITLE_PATTERNS:
            match = re.search(pattern, text[:2000], re.MULTILINE | re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                if title and len(title) < 200:  # Reasonable title length
                    return title

        # Fallback: use first non-empty line
        for line in text.split("\n")[:10]:
            line = line.strip()
            if line and len(line) > 10 and len(line) < 200:
                # Check if it looks like a title (not a sentence)
                if not line.endswith((".", ",", ";", ":")):
                    return line

        return None

    def estimate_language(self, text: str) -> str | None:
        """
        Estimate document language from content.

        Uses simple heuristics for common languages.
        Returns ISO 639-1 language code.
        """
        if not text or len(text) < 50:
            return None

        sample = text[:5000].lower()

        # Common word frequencies for language detection
        language_markers = {
            "en": ["the", "and", "is", "of", "to", "in", "that", "it"],
            "es": ["el", "la", "de", "que", "y", "en", "los", "del"],
            "fr": ["le", "la", "de", "et", "les", "des", "en", "un"],
            "de": ["der", "die", "und", "in", "den", "von", "zu", "das"],
            "it": ["il", "di", "che", "la", "e", "per", "un", "del"],
            "pt": ["de", "que", "e", "do", "da", "em", "para", "os"],
        }

        scores = {}
        for lang, markers in language_markers.items():
            score = sum(1 for word in markers if f" {word} " in sample)
            scores[lang] = score

        if scores:
            best_lang = max(scores, key=scores.get)
            if scores[best_lang] >= 3:  # Minimum threshold
                return best_lang

        return None

    def compute_fingerprint(self, text: str) -> str:
        """
        Compute a content fingerprint for similarity detection.

        Uses first N characters of normalized text hash.
        """
        # Normalize text
        normalized = re.sub(r"\s+", " ", text.lower().strip())
        # Hash
        return hashlib.md5(normalized[:10000].encode()).hexdigest()[:16]

    def enrich_metadata(
        self, document: ParsedDocument, custom_metadata: dict[str, Any] | None = None
    ) -> ParsedDocument:
        """
        Enrich document with additional extracted metadata.

        Args:
            document: Parsed document to enrich
            custom_metadata: Additional user-provided metadata

        Returns:
            Document with enriched metadata
        """
        metadata = document.metadata

        # Extract title if missing
        if not metadata.title and document.raw_text:
            metadata.title = self.extract_title(document.raw_text, metadata)

        # Estimate language if missing
        if not metadata.language and document.raw_text:
            metadata.language = self.estimate_language(document.raw_text)

        # Calculate word count if missing
        if not metadata.word_count:
            metadata.word_count = sum(
                len(block.text.split()) for block in document.content_blocks
            )

        # Add custom metadata
        if custom_metadata:
            metadata.custom_metadata.update(custom_metadata)

        return document

    def merge_metadata(
        self, base: DocumentMetadata, override: dict[str, Any]
    ) -> DocumentMetadata:
        """
        Merge additional metadata into existing metadata.

        Override values take precedence over existing values.
        """
        data = base.model_dump()

        for key, value in override.items():
            if key in data and value is not None:
                if key == "custom_metadata":
                    data[key].update(value)
                else:
                    data[key] = value

        return DocumentMetadata(**data)


def enrich_document(
    document: ParsedDocument, custom_metadata: dict[str, Any] | None = None
) -> ParsedDocument:
    """
    Convenience function to enrich document metadata.

    Args:
        document: Document to enrich
        custom_metadata: Optional additional metadata

    Returns:
        Enriched document
    """
    extractor = MetadataExtractor()
    return extractor.enrich_metadata(document, custom_metadata)
