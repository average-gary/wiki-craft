"""
HTML document parser.

Extracts clean text content from HTML pages with structure preservation.
"""

import logging
import re
from pathlib import Path
from typing import BinaryIO, ClassVar
from urllib.parse import urlparse

from wiki_craft.parsers.base import BaseParser
from wiki_craft.storage.models import (
    ContentBlock,
    ContentType,
    DocumentMetadata,
    DocumentType,
    ParsedDocument,
)

logger = logging.getLogger(__name__)


class HTMLParser(BaseParser):
    """Parser for HTML documents and web pages."""

    supported_extensions: ClassVar[list[str]] = ["html", "htm", "xhtml"]
    supported_mime_types: ClassVar[list[str]] = [
        "text/html",
        "application/xhtml+xml",
    ]
    document_type: ClassVar[DocumentType] = DocumentType.HTML

    # Tags to ignore (non-content)
    IGNORE_TAGS = {
        "script",
        "style",
        "noscript",
        "iframe",
        "svg",
        "canvas",
        "nav",
        "footer",
        "header",
        "aside",
        "form",
        "button",
        "input",
        "select",
        "textarea",
    }

    # Block-level tags
    BLOCK_TAGS = {
        "p",
        "div",
        "section",
        "article",
        "main",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "blockquote",
        "pre",
        "ul",
        "ol",
        "li",
        "table",
        "tr",
        "td",
        "th",
        "figure",
        "figcaption",
    }

    def parse(self, file_path: Path, file_content: BinaryIO | None = None) -> ParsedDocument:
        """
        Parse an HTML document.

        Args:
            file_path: Path to the HTML file (or URL for reference)
            file_content: Optional file-like object with content

        Returns:
            ParsedDocument with extracted content
        """
        from bs4 import BeautifulSoup

        self.errors = []

        try:
            # Load content
            if file_content is not None:
                content_bytes = file_content.read()
                source_hash = self.compute_hash(content_bytes)
                html = content_bytes.decode("utf-8", errors="replace")
            else:
                source_hash = self.compute_file_hash(file_path)
                html = file_path.read_text(encoding="utf-8", errors="replace")

            # Parse HTML
            soup = BeautifulSoup(html, "lxml")

            # Extract metadata
            metadata = self._extract_metadata(soup, file_path, source_hash)

            # Remove non-content elements
            for tag in soup.find_all(self.IGNORE_TAGS):
                tag.decompose()

            # Find main content area
            main_content = self._find_main_content(soup)

            # Extract content blocks
            content_blocks = self._extract_blocks(main_content)

            # Calculate word count
            metadata.word_count = sum(len(block.text.split()) for block in content_blocks)

            return ParsedDocument(
                metadata=metadata,
                content_blocks=content_blocks,
                raw_text="\n\n".join(block.text for block in content_blocks),
                parsing_errors=self.errors,
            )

        except Exception as e:
            self.add_error(f"Failed to parse HTML: {e}")
            raise

    def _extract_metadata(self, soup, file_path: Path, source_hash: str) -> DocumentMetadata:
        """Extract metadata from HTML."""
        title = None
        author = None

        # Get title
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text().strip()

        # Try meta tags
        meta_author = soup.find("meta", {"name": "author"})
        if meta_author:
            author = meta_author.get("content")

        # Try og:title if no title
        if not title:
            og_title = soup.find("meta", {"property": "og:title"})
            if og_title:
                title = og_title.get("content")

        return DocumentMetadata(
            source_path=str(file_path),
            source_hash=source_hash,
            filename=file_path.name,
            document_type=DocumentType.HTML,
            title=title,
            author=author,
        )

    def _find_main_content(self, soup):
        """Find the main content area of the page."""
        # Try semantic elements first
        for selector in ["main", "article", '[role="main"]', "#content", ".content", "#main"]:
            content = soup.select_one(selector)
            if content:
                return content

        # Fall back to body
        body = soup.find("body")
        return body if body else soup

    def _extract_blocks(self, element) -> list[ContentBlock]:
        """Extract content blocks from HTML element."""
        blocks = []
        current_section: str | None = None
        section_hierarchy: list[str] = []
        position = 0

        def process_element(el, depth=0):
            nonlocal current_section, section_hierarchy, position

            if el.name is None:  # NavigableString
                return

            tag_name = el.name.lower() if el.name else ""

            # Skip ignored tags
            if tag_name in self.IGNORE_TAGS:
                return

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
                            metadata={"level": level, "tag": tag_name},
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
                        )
                    )
                    position += 1
                return

            # Handle code blocks
            if tag_name == "pre":
                code = el.find("code")
                text = (code if code else el).get_text()
                if text.strip():
                    blocks.append(
                        ContentBlock(
                            text=text,
                            content_type=ContentType.CODE,
                            section=current_section,
                            section_hierarchy=section_hierarchy.copy(),
                            position=position,
                        )
                    )
                    position += 1
                return

            # Handle tables
            if tag_name == "table":
                table_text = self._extract_table(el)
                if table_text:
                    blocks.append(
                        ContentBlock(
                            text=table_text,
                            content_type=ContentType.TABLE,
                            section=current_section,
                            section_hierarchy=section_hierarchy.copy(),
                            position=position,
                        )
                    )
                    position += 1
                return

            # Recurse into children for container elements
            for child in el.children:
                if hasattr(child, "name"):
                    process_element(child, depth + 1)

        process_element(element)
        return blocks

    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _extract_table(self, table) -> str:
        """Extract table content as formatted text."""
        rows = []
        for tr in table.find_all("tr"):
            cells = []
            for cell in tr.find_all(["td", "th"]):
                cells.append(self._clean_text(cell.get_text()))
            if cells:
                rows.append(" | ".join(cells))
        return "\n".join(rows)
