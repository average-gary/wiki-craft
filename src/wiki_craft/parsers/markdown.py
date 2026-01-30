"""
Markdown and plain text document parser.

Handles .md, .txt, and .rst files with frontmatter support.
"""

import logging
import re
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


class MarkdownParser(BaseParser):
    """Parser for Markdown and plain text documents."""

    supported_extensions: ClassVar[list[str]] = ["md", "markdown", "txt", "rst", "text"]
    supported_mime_types: ClassVar[list[str]] = [
        "text/markdown",
        "text/plain",
        "text/x-rst",
    ]
    document_type: ClassVar[DocumentType] = DocumentType.MARKDOWN

    # Regex patterns
    HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
    ALT_HEADING_PATTERN = re.compile(r"^(.+)\n([=-])+$", re.MULTILINE)
    LIST_PATTERN = re.compile(r"^[\s]*[-*+]\s+.+$|^[\s]*\d+\.\s+.+$", re.MULTILINE)
    CODE_BLOCK_PATTERN = re.compile(r"```[\s\S]*?```|`[^`]+`", re.MULTILINE)
    BLOCKQUOTE_PATTERN = re.compile(r"^>\s*.+$", re.MULTILINE)

    def parse(self, file_path: Path, file_content: BinaryIO | None = None) -> ParsedDocument:
        """
        Parse a Markdown or text document.

        Args:
            file_path: Path to the file
            file_content: Optional file-like object with content

        Returns:
            ParsedDocument with extracted content
        """
        import frontmatter

        self.errors = []

        try:
            # Load content
            if file_content is not None:
                content_bytes = file_content.read()
                source_hash = self.compute_hash(content_bytes)
                text = content_bytes.decode("utf-8", errors="replace")
            else:
                source_hash = self.compute_file_hash(file_path)
                text = file_path.read_text(encoding="utf-8", errors="replace")

            # Parse frontmatter if present
            doc_metadata = {}
            try:
                post = frontmatter.loads(text)
                doc_metadata = dict(post.metadata)
                text = post.content
            except Exception:
                pass  # No frontmatter or invalid format

            # Determine document type based on extension
            ext = file_path.suffix.lower()
            doc_type = DocumentType.MARKDOWN if ext in [".md", ".markdown"] else DocumentType.TEXT

            # Extract metadata
            metadata = DocumentMetadata(
                source_path=str(file_path),
                source_hash=source_hash,
                filename=file_path.name,
                document_type=doc_type,
                title=doc_metadata.get("title"),
                author=doc_metadata.get("author"),
                custom_metadata=doc_metadata,
            )

            # Parse content into blocks
            content_blocks = self._parse_content(text)

            # Calculate word count
            metadata.word_count = sum(len(block.text.split()) for block in content_blocks)

            return ParsedDocument(
                metadata=metadata,
                content_blocks=content_blocks,
                raw_text=text,
                parsing_errors=self.errors,
            )

        except Exception as e:
            self.add_error(f"Failed to parse document: {e}")
            raise

    def _parse_content(self, text: str) -> list[ContentBlock]:
        """Parse text content into structured blocks."""
        blocks = []
        current_section: str | None = None
        section_hierarchy: list[str] = []
        position = 0

        # Split into lines for processing
        lines = text.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i]

            # Check for ATX-style headings (# Heading)
            heading_match = self.HEADING_PATTERN.match(line)
            if heading_match:
                level = len(heading_match.group(1))
                heading_text = heading_match.group(2).strip()

                # Update section hierarchy
                section_hierarchy = section_hierarchy[: level - 1] + [heading_text]
                current_section = heading_text

                blocks.append(
                    ContentBlock(
                        text=heading_text,
                        content_type=ContentType.HEADING,
                        section=current_section,
                        section_hierarchy=section_hierarchy.copy(),
                        position=position,
                        metadata={"level": level},
                    )
                )
                position += 1
                i += 1
                continue

            # Check for Setext-style headings (underlined with = or -)
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                if next_line and (
                    all(c == "=" for c in next_line.strip())
                    or all(c == "-" for c in next_line.strip())
                ):
                    if line.strip():
                        level = 1 if "=" in next_line else 2
                        heading_text = line.strip()
                        section_hierarchy = section_hierarchy[: level - 1] + [heading_text]
                        current_section = heading_text

                        blocks.append(
                            ContentBlock(
                                text=heading_text,
                                content_type=ContentType.HEADING,
                                section=current_section,
                                section_hierarchy=section_hierarchy.copy(),
                                position=position,
                                metadata={"level": level},
                            )
                        )
                        position += 1
                        i += 2
                        continue

            # Check for code blocks
            if line.strip().startswith("```"):
                code_lines = [line]
                i += 1
                while i < len(lines) and not lines[i].strip().startswith("```"):
                    code_lines.append(lines[i])
                    i += 1
                if i < len(lines):
                    code_lines.append(lines[i])
                    i += 1

                blocks.append(
                    ContentBlock(
                        text="\n".join(code_lines),
                        content_type=ContentType.CODE,
                        section=current_section,
                        section_hierarchy=section_hierarchy.copy(),
                        position=position,
                    )
                )
                position += 1
                continue

            # Check for blockquotes
            if line.strip().startswith(">"):
                quote_lines = []
                while i < len(lines) and lines[i].strip().startswith(">"):
                    quote_lines.append(lines[i].lstrip(">").strip())
                    i += 1

                blocks.append(
                    ContentBlock(
                        text="\n".join(quote_lines),
                        content_type=ContentType.QUOTE,
                        section=current_section,
                        section_hierarchy=section_hierarchy.copy(),
                        position=position,
                    )
                )
                position += 1
                continue

            # Check for list items
            if self.LIST_PATTERN.match(line):
                list_lines = []
                while i < len(lines) and (
                    self.LIST_PATTERN.match(lines[i]) or lines[i].startswith("  ")
                ):
                    list_lines.append(lines[i])
                    i += 1

                blocks.append(
                    ContentBlock(
                        text="\n".join(list_lines),
                        content_type=ContentType.LIST,
                        section=current_section,
                        section_hierarchy=section_hierarchy.copy(),
                        position=position,
                    )
                )
                position += 1
                continue

            # Regular paragraph
            if line.strip():
                para_lines = []
                while i < len(lines) and lines[i].strip() and not self._is_special_line(lines[i]):
                    para_lines.append(lines[i])
                    i += 1

                if para_lines:
                    blocks.append(
                        ContentBlock(
                            text=" ".join(para_lines),
                            content_type=ContentType.PARAGRAPH,
                            section=current_section,
                            section_hierarchy=section_hierarchy.copy(),
                            position=position,
                        )
                    )
                    position += 1
                continue

            i += 1

        return blocks

    def _is_special_line(self, line: str) -> bool:
        """Check if a line is a special markdown element."""
        stripped = line.strip()
        return (
            stripped.startswith("#")
            or stripped.startswith(">")
            or stripped.startswith("```")
            or self.LIST_PATTERN.match(line) is not None
            or all(c == "=" for c in stripped)
            or all(c == "-" for c in stripped)
        )
