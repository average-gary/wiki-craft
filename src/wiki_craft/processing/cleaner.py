"""
Text cleaning and normalization utilities.

Prepares text for embedding by removing noise while preserving meaning.
"""

import re
import unicodedata
from typing import Callable


class TextCleaner:
    """
    Cleans and normalizes text for embedding and display.

    Handles:
    - Unicode normalization
    - Whitespace cleanup
    - Special character handling
    - Optional HTML stripping
    - Configurable cleaning pipelines
    """

    def __init__(self, aggressive: bool = False) -> None:
        """
        Initialize the cleaner.

        Args:
            aggressive: If True, apply more aggressive cleaning
        """
        self.aggressive = aggressive

    def clean(self, text: str) -> str:
        """
        Apply standard cleaning pipeline.

        Args:
            text: Raw text to clean

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Unicode normalization
        text = self.normalize_unicode(text)

        # Whitespace normalization
        text = self.normalize_whitespace(text)

        # Remove control characters
        text = self.remove_control_chars(text)

        if self.aggressive:
            # Additional aggressive cleaning
            text = self.remove_urls(text)
            text = self.remove_email_addresses(text)

        return text.strip()

    def clean_for_embedding(self, text: str) -> str:
        """
        Clean text optimized for embedding generation.

        Preserves semantic meaning while removing noise.
        """
        text = self.clean(text)

        # Remove excessive punctuation
        text = re.sub(r"([.!?])\1+", r"\1", text)

        # Normalize quotes
        text = self.normalize_quotes(text)

        # Remove very short lines (likely noise)
        lines = text.split("\n")
        lines = [line for line in lines if len(line.strip()) > 3]
        text = "\n".join(lines)

        return text.strip()

    def clean_for_display(self, text: str) -> str:
        """
        Clean text optimized for human reading.

        Preserves formatting while fixing common issues.
        """
        text = self.clean(text)

        # Fix spacing around punctuation
        text = re.sub(r"\s+([.,;:!?])", r"\1", text)
        text = re.sub(r"([.,;:!?])([A-Za-z])", r"\1 \2", text)

        return text.strip()

    @staticmethod
    def normalize_unicode(text: str) -> str:
        """Normalize unicode characters to NFC form."""
        return unicodedata.normalize("NFC", text)

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """
        Normalize whitespace while preserving paragraph breaks.

        - Collapses multiple spaces to single space
        - Preserves single newlines
        - Collapses multiple newlines to double newline
        """
        # Replace tabs with spaces
        text = text.replace("\t", " ")

        # Collapse multiple spaces
        text = re.sub(r" +", " ", text)

        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Collapse multiple newlines (preserve paragraph breaks)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Remove trailing whitespace on lines
        lines = [line.rstrip() for line in text.split("\n")]
        text = "\n".join(lines)

        return text

    @staticmethod
    def remove_control_chars(text: str) -> str:
        """Remove control characters except newlines and tabs."""
        # Keep: \n (10), \t (9), standard printable characters
        return "".join(
            char
            for char in text
            if unicodedata.category(char) != "Cc" or char in "\n\t"
        )

    @staticmethod
    def remove_urls(text: str) -> str:
        """Remove URLs from text."""
        url_pattern = r"https?://[^\s<>\"{}|\\^`\[\]]+"
        return re.sub(url_pattern, "", text)

    @staticmethod
    def remove_email_addresses(text: str) -> str:
        """Remove email addresses from text."""
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        return re.sub(email_pattern, "", text)

    @staticmethod
    def normalize_quotes(text: str) -> str:
        """Normalize various quote characters to standard ASCII quotes."""
        # Single quotes
        text = re.sub(r"[''‚‛]", "'", text)
        # Double quotes
        text = re.sub(r"[""„‟]", '"', text)
        return text

    @staticmethod
    def strip_html(text: str) -> str:
        """Remove HTML tags from text."""
        # Remove tags
        text = re.sub(r"<[^>]+>", " ", text)
        # Decode common entities
        text = text.replace("&nbsp;", " ")
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')
        text = text.replace("&#39;", "'")
        return text

    @staticmethod
    def truncate(text: str, max_length: int, suffix: str = "...") -> str:
        """
        Truncate text to max length, breaking at word boundary.

        Args:
            text: Text to truncate
            max_length: Maximum length including suffix
            suffix: String to append when truncated

        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text

        # Find last space before max_length
        truncate_at = max_length - len(suffix)
        last_space = text.rfind(" ", 0, truncate_at)

        if last_space > 0:
            return text[:last_space] + suffix
        else:
            return text[:truncate_at] + suffix


def clean_text(text: str, aggressive: bool = False) -> str:
    """
    Convenience function for text cleaning.

    Args:
        text: Text to clean
        aggressive: Apply aggressive cleaning

    Returns:
        Cleaned text
    """
    cleaner = TextCleaner(aggressive=aggressive)
    return cleaner.clean(text)


def clean_for_embedding(text: str) -> str:
    """Clean text for embedding generation."""
    cleaner = TextCleaner()
    return cleaner.clean_for_embedding(text)
