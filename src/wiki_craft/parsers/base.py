"""
Base parser interface and registry.

All document parsers inherit from BaseParser and implement the parse method.
The ParserRegistry provides automatic parser selection based on file type.
"""

import hashlib
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, ClassVar

from wiki_craft.storage.models import DocumentType, ParsedDocument

logger = logging.getLogger(__name__)


class BaseParser(ABC):
    """
    Abstract base class for document parsers.

    Each parser handles one or more file types and extracts content
    with full metadata for provenance tracking.
    """

    # Subclasses must define supported extensions and MIME types
    supported_extensions: ClassVar[list[str]] = []
    supported_mime_types: ClassVar[list[str]] = []
    document_type: ClassVar[DocumentType] = DocumentType.UNKNOWN

    def __init__(self) -> None:
        """Initialize the parser."""
        self.errors: list[str] = []

    @abstractmethod
    def parse(self, file_path: Path, file_content: BinaryIO | None = None) -> ParsedDocument:
        """
        Parse a document and extract content with metadata.

        Args:
            file_path: Path to the document file
            file_content: Optional file-like object with content (for uploads)

        Returns:
            ParsedDocument with extracted content blocks and metadata
        """
        pass

    @classmethod
    def can_parse(cls, file_path: Path, mime_type: str | None = None) -> bool:
        """
        Check if this parser can handle the given file.

        Args:
            file_path: Path to check
            mime_type: Optional MIME type hint

        Returns:
            True if this parser can handle the file
        """
        ext = file_path.suffix.lower().lstrip(".")
        if ext in cls.supported_extensions:
            return True
        if mime_type and mime_type in cls.supported_mime_types:
            return True
        return False

    @staticmethod
    def compute_hash(content: bytes) -> str:
        """Compute SHA-256 hash of content for deduplication."""
        return hashlib.sha256(content).hexdigest()

    @staticmethod
    def compute_file_hash(file_path: Path) -> str:
        """Compute SHA-256 hash of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def add_error(self, error: str) -> None:
        """Record a non-fatal parsing error."""
        self.errors.append(error)
        logger.warning(f"Parser error: {error}")


class ParserRegistry:
    """
    Registry of available document parsers.

    Provides automatic parser selection based on file extension or MIME type.
    """

    _parsers: ClassVar[list[type[BaseParser]]] = []

    @classmethod
    def register(cls, parser_class: type[BaseParser]) -> None:
        """Register a parser class."""
        if parser_class not in cls._parsers:
            cls._parsers.append(parser_class)
            logger.debug(f"Registered parser: {parser_class.__name__}")

    @classmethod
    def get_parser(cls, file_path: Path, mime_type: str | None = None) -> BaseParser | None:
        """
        Get an appropriate parser for a file.

        Args:
            file_path: Path to the file
            mime_type: Optional MIME type hint

        Returns:
            Parser instance or None if no parser found
        """
        for parser_class in cls._parsers:
            if parser_class.can_parse(file_path, mime_type):
                return parser_class()
        return None

    @classmethod
    def get_supported_extensions(cls) -> list[str]:
        """Get list of all supported file extensions."""
        extensions = []
        for parser_class in cls._parsers:
            extensions.extend(parser_class.supported_extensions)
        return list(set(extensions))

    @classmethod
    def get_parser_for_type(cls, doc_type: DocumentType) -> BaseParser | None:
        """Get a parser for a specific document type."""
        for parser_class in cls._parsers:
            if parser_class.document_type == doc_type:
                return parser_class()
        return None
