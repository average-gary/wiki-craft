"""Tests for the Markdown parser."""

import tempfile
from pathlib import Path

import pytest

from wiki_craft.parsers.markdown import MarkdownParser
from wiki_craft.storage.models import ContentType


class TestMarkdownParser:
    """Test suite for MarkdownParser."""

    def test_can_parse_markdown_files(self):
        """Test that parser recognizes markdown files."""
        parser = MarkdownParser

        assert parser.can_parse(Path("test.md"))
        assert parser.can_parse(Path("test.markdown"))
        assert parser.can_parse(Path("test.txt"))
        assert not parser.can_parse(Path("test.pdf"))
        assert not parser.can_parse(Path("test.docx"))

    def test_parse_simple_markdown(self, sample_markdown: str, temp_dir: Path):
        """Test parsing a simple markdown document."""
        # Write sample to file
        md_file = temp_dir / "test.md"
        md_file.write_text(sample_markdown)

        parser = MarkdownParser()
        document = parser.parse(md_file)

        # Check metadata
        assert document.metadata.filename == "test.md"
        assert document.metadata.source_path == str(md_file)
        assert document.metadata.source_hash is not None

        # Check content blocks were extracted
        assert len(document.content_blocks) > 0

        # Check headings were identified
        headings = [b for b in document.content_blocks if b.content_type == ContentType.HEADING]
        assert len(headings) >= 3  # At least h1, h2, h2

        # Check section hierarchy
        assert document.content_blocks[0].content_type == ContentType.HEADING
        assert document.content_blocks[0].text == "Sample Document"

    def test_parse_with_frontmatter(self, temp_dir: Path):
        """Test parsing markdown with YAML frontmatter."""
        content = """---
title: My Document
author: Test Author
date: 2024-01-15
---

# Content

This is the document content.
"""
        md_file = temp_dir / "frontmatter.md"
        md_file.write_text(content)

        parser = MarkdownParser()
        document = parser.parse(md_file)

        # Custom metadata should be extracted
        assert document.metadata.title == "My Document"
        assert document.metadata.author == "Test Author"

    def test_parse_lists(self, temp_dir: Path):
        """Test that lists are correctly identified."""
        content = """# Lists

- Item 1
- Item 2
- Item 3

1. First
2. Second
3. Third
"""
        md_file = temp_dir / "lists.md"
        md_file.write_text(content)

        parser = MarkdownParser()
        document = parser.parse(md_file)

        lists = [b for b in document.content_blocks if b.content_type == ContentType.LIST]
        assert len(lists) >= 1

    def test_parse_code_blocks(self, temp_dir: Path):
        """Test that code blocks are correctly identified."""
        content = """# Code Example

```python
def hello():
    print("Hello, World!")
```

Some text after code.
"""
        md_file = temp_dir / "code.md"
        md_file.write_text(content)

        parser = MarkdownParser()
        document = parser.parse(md_file)

        code_blocks = [b for b in document.content_blocks if b.content_type == ContentType.CODE]
        assert len(code_blocks) >= 1

    def test_parse_blockquotes(self, temp_dir: Path):
        """Test that blockquotes are correctly identified."""
        content = """# Quote

> This is a blockquote.
> It spans multiple lines.

Regular paragraph.
"""
        md_file = temp_dir / "quote.md"
        md_file.write_text(content)

        parser = MarkdownParser()
        document = parser.parse(md_file)

        quotes = [b for b in document.content_blocks if b.content_type == ContentType.QUOTE]
        assert len(quotes) >= 1

    def test_section_hierarchy(self, temp_dir: Path):
        """Test that section hierarchy is correctly tracked."""
        content = """# Top Level

## Section A

### Subsection A.1

Content here.

## Section B

More content.
"""
        md_file = temp_dir / "hierarchy.md"
        md_file.write_text(content)

        parser = MarkdownParser()
        document = parser.parse(md_file)

        # Find the subsection content
        for block in document.content_blocks:
            if "Content here" in block.text:
                assert "Subsection A.1" in block.section_hierarchy
                break
