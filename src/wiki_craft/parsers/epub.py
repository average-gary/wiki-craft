"""
EPUB e-book parser.

Extracts content from EPUB files with chapter structure preservation.
"""

import logging
from pathlib import Path
from typing import BinaryIO, ClassVar

from wiki_craft.parsers.base import BaseParser
from wiki_craft.storage.models import (
    ContentBlock,
    ContentType,
    DocumentMetadata,
    DocumentType,
    ParsedDocument,
)

logger = logging.getLogger(__name__)


class EPUBParser(BaseParser):
    """Parser for EPUB e-books."""

    supported_extensions: ClassVar[list[str]] = ["epub"]
    supported_mime_types: ClassVar[list[str]] = ["application/epub+zip"]
    document_type: ClassVar[DocumentType] = DocumentType.EPUB

    def parse(self, file_path: Path, file_content: BinaryIO | None = None) -> ParsedDocument:
        """
        Parse an EPUB e-book.

        Args:
            file_path: Path to the EPUB file
            file_content: Optional file-like object with content

        Returns:
            ParsedDocument with extracted content
        """
        import ebooklib
        from bs4 import BeautifulSoup
        from ebooklib import epub

        self.errors = []

        try:
            # Load EPUB
            if file_content is not None:
                content_bytes = file_content.read()
                source_hash = self.compute_hash(content_bytes)
                import io
                import tempfile

                # ebooklib needs a file path, so create temp file
                with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as tmp:
                    tmp.write(content_bytes)
                    tmp_path = tmp.name

                book = epub.read_epub(tmp_path)
                # Clean up temp file
                Path(tmp_path).unlink()
            else:
                source_hash = self.compute_file_hash(file_path)
                book = epub.read_epub(str(file_path))

            # Extract metadata
            metadata = self._extract_metadata(book, file_path, source_hash)

            # Extract content
            content_blocks = []
            position = 0
            chapter_num = 0

            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    chapter_num += 1
                    chapter_blocks = self._parse_chapter(item, chapter_num, position)
                    position += len(chapter_blocks)
                    content_blocks.extend(chapter_blocks)

            # Calculate word count
            metadata.word_count = sum(len(block.text.split()) for block in content_blocks)

            return ParsedDocument(
                metadata=metadata,
                content_blocks=content_blocks,
                raw_text="\n\n".join(block.text for block in content_blocks),
                parsing_errors=self.errors,
            )

        except Exception as e:
            self.add_error(f"Failed to parse EPUB: {e}")
            raise

    def _extract_metadata(self, book, file_path: Path, source_hash: str) -> DocumentMetadata:
        """Extract metadata from EPUB."""
        title = None
        author = None

        # Get title
        titles = book.get_metadata("DC", "title")
        if titles:
            title = titles[0][0]

        # Get author
        creators = book.get_metadata("DC", "creator")
        if creators:
            author = creators[0][0]

        return DocumentMetadata(
            source_path=str(file_path),
            source_hash=source_hash,
            filename=file_path.name,
            document_type=DocumentType.EPUB,
            title=title,
            author=author,
        )

    def _parse_chapter(self, item, chapter_num: int, start_position: int) -> list[ContentBlock]:
        """Parse a single chapter/document item."""
        from bs4 import BeautifulSoup
        import re

        blocks = []
        position = start_position

        # Parse HTML content
        content = item.get_content().decode("utf-8", errors="replace")
        soup = BeautifulSoup(content, "lxml")

        # Remove scripts and styles
        for tag in soup.find_all(["script", "style"]):
            tag.decompose()

        # Get body content
        body = soup.find("body")
        if not body:
            body = soup

        current_section: str | None = None
        section_hierarchy: list[str] = []

        def process_element(el):
            nonlocal current_section, section_hierarchy, position

            if el.name is None:
                return

            tag_name = el.name.lower() if el.name else ""

            # Handle headings
            if tag_name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                text = el.get_text().strip()
                if text:
                    level = int(tag_name[1])
                    section_hierarchy = section_hierarchy[: level - 1] + [text]
                    current_section = text

                    blocks.append(
                        ContentBlock(
                            text=text,
                            content_type=ContentType.HEADING,
                            section=current_section,
                            section_hierarchy=section_hierarchy.copy(),
                            position=position,
                            metadata={"level": level, "chapter": chapter_num},
                        )
                    )
                    position += 1
                return

            # Handle paragraphs
            if tag_name == "p":
                text = self._clean_text(el.get_text())
                if text:
                    blocks.append(
                        ContentBlock(
                            text=text,
                            content_type=ContentType.PARAGRAPH,
                            section=current_section,
                            section_hierarchy=section_hierarchy.copy(),
                            position=position,
                            metadata={"chapter": chapter_num},
                        )
                    )
                    position += 1
                return

            # Handle lists
            if tag_name in ["ul", "ol"]:
                items = []
                for li in el.find_all("li", recursive=False):
                    item_text = self._clean_text(li.get_text())
                    if item_text:
                        items.append(f"- {item_text}")
                if items:
                    blocks.append(
                        ContentBlock(
                            text="\n".join(items),
                            content_type=ContentType.LIST,
                            section=current_section,
                            section_hierarchy=section_hierarchy.copy(),
                            position=position,
                            metadata={"chapter": chapter_num},
                        )
                    )
                    position += 1
                return

            # Handle blockquotes
            if tag_name == "blockquote":
                text = self._clean_text(el.get_text())
                if text:
                    blocks.append(
                        ContentBlock(
                            text=text,
                            content_type=ContentType.QUOTE,
                            section=current_section,
                            section_hierarchy=section_hierarchy.copy(),
                            position=position,
                            metadata={"chapter": chapter_num},
                        )
                    )
                    position += 1
                return

            # Handle divs and other containers
            if tag_name in ["div", "section", "article", "main"]:
                for child in el.children:
                    if hasattr(child, "name"):
                        process_element(child)
                return

            # For other elements, try to get text
            for child in el.children:
                if hasattr(child, "name"):
                    process_element(child)

        for child in body.children:
            if hasattr(child, "name"):
                process_element(child)

        return blocks

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        import re
        text = re.sub(r"\s+", " ", text)
        return text.strip()
