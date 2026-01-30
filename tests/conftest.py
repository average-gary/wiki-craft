"""
Pytest configuration and fixtures for Wiki-Craft tests.
"""

import tempfile
from pathlib import Path
from typing import Generator

import pytest

from wiki_craft.config import Settings
from wiki_craft.storage.vector_store import VectorStore


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_settings(temp_dir: Path) -> Settings:
    """Create test settings with temporary directories."""
    return Settings(
        data_dir=temp_dir,
        chromadb_dir=temp_dir / "chromadb",
        uploads_dir=temp_dir / "uploads",
        chroma_collection_name="test_collection",
        embedding_model="all-MiniLM-L6-v2",  # Smaller model for faster tests
        embedding_device="cpu",
    )


@pytest.fixture
def vector_store(test_settings: Settings) -> Generator[VectorStore, None, None]:
    """Create a test vector store."""
    test_settings.ensure_directories()

    store = VectorStore(
        persist_directory=str(test_settings.chromadb_dir),
        collection_name=test_settings.chroma_collection_name,
    )
    yield store

    # Cleanup
    VectorStore.reset_instance()


@pytest.fixture
def sample_markdown() -> str:
    """Sample markdown content for testing."""
    return """# Sample Document

This is a sample document for testing the Wiki-Craft system.

## Introduction

The introduction section provides an overview of the topic.
It contains multiple paragraphs of text.

This is the second paragraph of the introduction.

## Main Content

### Subsection 1

Here is some content in subsection 1.

- List item 1
- List item 2
- List item 3

### Subsection 2

Here is some content in subsection 2.

> This is a blockquote with important information.

## Conclusion

The conclusion wraps up the document.
"""


@pytest.fixture
def sample_html() -> str:
    """Sample HTML content for testing."""
    return """<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
</head>
<body>
    <h1>Test Document</h1>
    <p>This is a test paragraph.</p>
    <h2>Section One</h2>
    <p>Content for section one.</p>
    <ul>
        <li>Item A</li>
        <li>Item B</li>
    </ul>
    <h2>Section Two</h2>
    <p>Content for section two.</p>
</body>
</html>
"""
