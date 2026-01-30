"""Text processing pipeline for Wiki-Craft."""

from wiki_craft.processing.chunker import SemanticChunker
from wiki_craft.processing.cleaner import TextCleaner
from wiki_craft.processing.metadata import MetadataExtractor

__all__ = [
    "SemanticChunker",
    "TextCleaner",
    "MetadataExtractor",
]
