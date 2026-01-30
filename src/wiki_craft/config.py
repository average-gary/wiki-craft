"""
Configuration management for Wiki-Craft.

Uses pydantic-settings for environment variable support and validation.
"""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="WIKICRAFT_",
        case_sensitive=False,
    )

    # Application
    app_name: str = "Wiki-Craft"
    debug: bool = False
    log_level: str = "INFO"

    # API Server
    host: str = "0.0.0.0"
    port: int = 8000
    api_prefix: str = "/api/v1"

    # Data Storage
    data_dir: Path = Field(default=Path("data"))
    chromadb_dir: Path = Field(default=Path("data/chromadb"))
    uploads_dir: Path = Field(default=Path("data/uploads"))

    # Embedding Model
    embedding_model: str = "all-mpnet-base-v2"
    embedding_device: str = "cpu"  # "cpu", "cuda", "mps"
    embedding_batch_size: int = 32

    # ChromaDB
    chroma_collection_name: str = "wiki_craft_documents"

    # Chunking
    chunk_size: int = 1000  # Target chunk size in characters
    chunk_overlap: int = 200  # Overlap between chunks
    min_chunk_size: int = 100  # Minimum chunk size
    max_chunk_size: int = 2000  # Maximum chunk size

    # OCR Settings
    ocr_enabled: bool = True
    ocr_language: str = "eng"  # Tesseract language code
    ocr_dpi: int = 300  # DPI for image conversion

    # Search
    default_search_limit: int = 10
    max_search_limit: int = 100

    # Wiki Generation
    wiki_output_format: Literal["markdown", "html", "json"] = "markdown"
    max_sources_per_section: int = 5

    def ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.chromadb_dir.mkdir(parents=True, exist_ok=True)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
