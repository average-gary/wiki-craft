"""
PDF document parser with OCR support.

Uses PyMuPDF (fitz) for text extraction and Tesseract for scanned pages.
"""

import io
import logging
from datetime import datetime
from pathlib import Path
from typing import BinaryIO, ClassVar

import fitz  # PyMuPDF

from wiki_craft.config import settings
from wiki_craft.parsers.base import BaseParser
from wiki_craft.storage.models import (
    ContentBlock,
    ContentType,
    DocumentMetadata,
    DocumentType,
    ParsedDocument,
)

logger = logging.getLogger(__name__)


class PDFParser(BaseParser):
    """Parser for PDF documents with OCR fallback for scanned pages."""

    supported_extensions: ClassVar[list[str]] = ["pdf"]
    supported_mime_types: ClassVar[list[str]] = ["application/pdf"]
    document_type: ClassVar[DocumentType] = DocumentType.PDF

    # Minimum text length to consider a page as having extractable text
    MIN_TEXT_LENGTH = 50

    def parse(self, file_path: Path, file_content: BinaryIO | None = None) -> ParsedDocument:
        """
        Parse a PDF document.

        Args:
            file_path: Path to the PDF file
            file_content: Optional file-like object with PDF content

        Returns:
            ParsedDocument with extracted text and metadata
        """
        self.errors = []

        # Load document
        if file_content is not None:
            content_bytes = file_content.read()
            doc = fitz.open(stream=content_bytes, filetype="pdf")
            source_hash = self.compute_hash(content_bytes)
        else:
            doc = fitz.open(file_path)
            source_hash = self.compute_file_hash(file_path)

        try:
            # Extract metadata
            metadata = self._extract_metadata(doc, file_path, source_hash)

            # Extract content blocks
            content_blocks = []
            current_section: str | None = None
            section_hierarchy: list[str] = []
            position = 0

            for page_num in range(len(doc)):
                page = doc[page_num]
                page_number = page_num + 1  # 1-indexed

                # Try text extraction first
                text = page.get_text("text").strip()

                # If minimal text, try OCR
                if len(text) < self.MIN_TEXT_LENGTH and settings.ocr_enabled:
                    ocr_text = self._ocr_page(page)
                    if ocr_text:
                        text = ocr_text

                if not text:
                    continue

                # Try to extract structured blocks
                blocks = self._extract_blocks(page, page_number, position, section_hierarchy)

                if blocks:
                    # Update section hierarchy from headings
                    for block in blocks:
                        if block.content_type == ContentType.HEADING:
                            current_section = block.text
                            # Simple hierarchy: reset on new heading
                            section_hierarchy = [current_section]
                        block.section = current_section
                        block.section_hierarchy = section_hierarchy.copy()
                    content_blocks.extend(blocks)
                    position += len(blocks)
                else:
                    # Fallback: treat entire page as paragraphs
                    paragraphs = self._split_paragraphs(text)
                    for para in paragraphs:
                        if para.strip():
                            content_blocks.append(
                                ContentBlock(
                                    text=para.strip(),
                                    content_type=ContentType.PARAGRAPH,
                                    page_number=page_number,
                                    section=current_section,
                                    section_hierarchy=section_hierarchy.copy(),
                                    position=position,
                                )
                            )
                            position += 1

            # Calculate word count
            total_words = sum(len(block.text.split()) for block in content_blocks)
            metadata.word_count = total_words

            return ParsedDocument(
                metadata=metadata,
                content_blocks=content_blocks,
                raw_text="\n\n".join(block.text for block in content_blocks),
                parsing_errors=self.errors,
            )

        finally:
            doc.close()

    def _extract_metadata(
        self, doc: fitz.Document, file_path: Path, source_hash: str
    ) -> DocumentMetadata:
        """Extract document metadata from PDF."""
        pdf_metadata = doc.metadata or {}

        # Parse dates
        created_at = None
        modified_at = None

        if pdf_metadata.get("creationDate"):
            created_at = self._parse_pdf_date(pdf_metadata["creationDate"])
        if pdf_metadata.get("modDate"):
            modified_at = self._parse_pdf_date(pdf_metadata["modDate"])

        return DocumentMetadata(
            source_path=str(file_path),
            source_hash=source_hash,
            filename=file_path.name,
            document_type=DocumentType.PDF,
            title=pdf_metadata.get("title") or None,
            author=pdf_metadata.get("author") or None,
            created_at=created_at,
            modified_at=modified_at,
            page_count=len(doc),
        )

    def _parse_pdf_date(self, date_str: str) -> datetime | None:
        """Parse PDF date format (D:YYYYMMDDHHmmSS)."""
        try:
            # Remove 'D:' prefix if present
            if date_str.startswith("D:"):
                date_str = date_str[2:]
            # Handle timezone suffix
            date_str = date_str.split("+")[0].split("-")[0].split("Z")[0]
            # Parse basic format
            if len(date_str) >= 14:
                return datetime.strptime(date_str[:14], "%Y%m%d%H%M%S")
            elif len(date_str) >= 8:
                return datetime.strptime(date_str[:8], "%Y%m%d")
        except ValueError as e:
            self.add_error(f"Failed to parse PDF date '{date_str}': {e}")
        return None

    def _extract_blocks(
        self, page: fitz.Page, page_number: int, start_position: int, section_hierarchy: list[str]
    ) -> list[ContentBlock]:
        """
        Extract structured content blocks from a page.

        Uses PyMuPDF's text block extraction for better structure.
        """
        blocks = []
        position = start_position

        # Get text blocks with position info
        text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)

        for block in text_dict.get("blocks", []):
            if block.get("type") != 0:  # Skip non-text blocks
                continue

            block_text = ""
            max_font_size = 0

            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    block_text += span.get("text", "")
                    font_size = span.get("size", 12)
                    if font_size > max_font_size:
                        max_font_size = font_size

            block_text = block_text.strip()
            if not block_text:
                continue

            # Determine content type based on font size and formatting
            content_type = ContentType.PARAGRAPH
            if max_font_size > 14:  # Likely a heading
                content_type = ContentType.HEADING
            elif block_text.startswith(("- ", "* ", "• ", "1.", "2.", "3.")):
                content_type = ContentType.LIST

            blocks.append(
                ContentBlock(
                    text=block_text,
                    content_type=content_type,
                    page_number=page_number,
                    position=position,
                    metadata={"font_size": max_font_size},
                )
            )
            position += 1

        return blocks

    def _split_paragraphs(self, text: str) -> list[str]:
        """Split text into paragraphs."""
        # Split on double newlines or multiple newlines
        import re

        paragraphs = re.split(r"\n\s*\n", text)
        return [p.strip() for p in paragraphs if p.strip()]

    def _ocr_page(self, page: fitz.Page) -> str | None:
        """
        Perform OCR on a page using Tesseract.

        Returns extracted text or None if OCR fails.
        """
        try:
            import pytesseract
            from PIL import Image

            # Render page to image
            mat = fitz.Matrix(settings.ocr_dpi / 72, settings.ocr_dpi / 72)
            pix = page.get_pixmap(matrix=mat)

            # Convert to PIL Image
            img = Image.open(io.BytesIO(pix.tobytes("png")))

            # Run OCR
            text = pytesseract.image_to_string(img, lang=settings.ocr_language)
            return text.strip() if text else None

        except ImportError:
            self.add_error("pytesseract not available for OCR")
            return None
        except Exception as e:
            self.add_error(f"OCR failed: {e}")
            return None
