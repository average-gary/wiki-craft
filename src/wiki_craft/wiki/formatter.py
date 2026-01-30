"""
Wiki content formatting utilities.

Provides multiple output formats for wiki entries.
"""

import json
from typing import Any

from wiki_craft.storage.models import WikiEntry, WikiSection, WikiSource


class WikiFormatter:
    """
    Formats wiki entries for different output formats.

    Supports:
    - Markdown
    - HTML
    - JSON
    - Plain text
    """

    @staticmethod
    def to_markdown(entry: WikiEntry, include_sources: bool = True) -> str:
        """
        Format wiki entry as Markdown.

        Args:
            entry: WikiEntry to format
            include_sources: Include references section

        Returns:
            Markdown formatted string
        """
        lines = [f"# {entry.title}", ""]

        if entry.summary:
            lines.extend([entry.summary, ""])

        # Table of contents for entries with multiple sections
        if len(entry.sections) > 2:
            lines.append("## Contents")
            lines.append("")
            for i, section in enumerate(entry.sections, 1):
                anchor = section.heading.lower().replace(" ", "-")
                lines.append(f"{i}. [{section.heading}](#{anchor})")
            lines.append("")

        # Sections
        for section in entry.sections:
            lines.extend(_format_section_markdown(section, level=2, include_sources=include_sources))

        # References
        if include_sources and entry.all_sources:
            lines.extend(["", "## References", ""])
            for i, source in enumerate(entry.all_sources, 1):
                citation = _format_citation(source)
                lines.append(f"{i}. {citation}")

        # Footer
        lines.extend([
            "",
            "---",
            f"*Generated from {len(entry.all_sources)} sources*",
        ])

        return "\n".join(lines)

    @staticmethod
    def to_html(entry: WikiEntry, include_sources: bool = True) -> str:
        """
        Format wiki entry as HTML.

        Args:
            entry: WikiEntry to format
            include_sources: Include references section

        Returns:
            HTML formatted string
        """
        html_parts = [
            '<!DOCTYPE html>',
            '<html lang="en">',
            '<head>',
            f'<title>{entry.title}</title>',
            '<meta charset="UTF-8">',
            '<style>',
            'body { font-family: system-ui, sans-serif; max-width: 800px; margin: 0 auto; padding: 2rem; }',
            'h1 { border-bottom: 2px solid #333; padding-bottom: 0.5rem; }',
            '.summary { font-size: 1.1rem; color: #555; }',
            '.section { margin: 2rem 0; }',
            '.source { font-size: 0.9rem; color: #666; }',
            '.references { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #ddd; }',
            '.confidence { font-size: 0.8rem; color: #999; }',
            '</style>',
            '</head>',
            '<body>',
            '<article>',
            f'<h1>{entry.title}</h1>',
        ]

        if entry.summary:
            html_parts.append(f'<p class="summary">{entry.summary}</p>')

        # Sections
        for section in entry.sections:
            html_parts.extend(_format_section_html(section, level=2, include_sources=include_sources))

        # References
        if include_sources and entry.all_sources:
            html_parts.append('<section class="references">')
            html_parts.append('<h2>References</h2>')
            html_parts.append('<ol>')
            for source in entry.all_sources:
                citation = _format_citation(source)
                html_parts.append(f'<li>{citation}</li>')
            html_parts.append('</ol>')
            html_parts.append('</section>')

        html_parts.extend([
            '</article>',
            '</body>',
            '</html>',
        ])

        return "\n".join(html_parts)

    @staticmethod
    def to_json(entry: WikiEntry) -> str:
        """
        Format wiki entry as JSON.

        Args:
            entry: WikiEntry to format

        Returns:
            JSON formatted string
        """
        return json.dumps(entry.to_json_dict(), indent=2, default=str)

    @staticmethod
    def to_plain_text(entry: WikiEntry, include_sources: bool = True) -> str:
        """
        Format wiki entry as plain text.

        Args:
            entry: WikiEntry to format
            include_sources: Include references section

        Returns:
            Plain text formatted string
        """
        lines = [entry.title.upper(), "=" * len(entry.title), ""]

        if entry.summary:
            lines.extend([entry.summary, ""])

        for section in entry.sections:
            lines.extend(_format_section_plain(section, level=0, include_sources=include_sources))

        if include_sources and entry.all_sources:
            lines.extend(["", "REFERENCES", "-" * 10, ""])
            for i, source in enumerate(entry.all_sources, 1):
                citation = _format_citation(source)
                lines.append(f"[{i}] {citation}")

        return "\n".join(lines)

    @staticmethod
    def format(
        entry: WikiEntry,
        format_type: str = "markdown",
        include_sources: bool = True,
    ) -> str:
        """
        Format wiki entry to specified format.

        Args:
            entry: WikiEntry to format
            format_type: Output format (markdown, html, json, text)
            include_sources: Include references

        Returns:
            Formatted string
        """
        formatters = {
            "markdown": WikiFormatter.to_markdown,
            "html": WikiFormatter.to_html,
            "json": WikiFormatter.to_json,
            "text": WikiFormatter.to_plain_text,
        }

        formatter = formatters.get(format_type.lower())
        if not formatter:
            raise ValueError(f"Unknown format: {format_type}")

        if format_type == "json":
            return formatter(entry)
        return formatter(entry, include_sources)


def _format_section_markdown(
    section: WikiSection,
    level: int,
    include_sources: bool,
) -> list[str]:
    """Format a section as Markdown."""
    lines = []
    prefix = "#" * level

    lines.append(f"{prefix} {section.heading}")
    lines.append("")
    lines.append(section.content)
    lines.append("")

    # Inline source citations
    if include_sources and section.sources:
        source_refs = ", ".join(
            f"[{s.document_title or s.source_path}]" for s in section.sources[:3]
        )
        lines.append(f"*Sources: {source_refs}*")
        lines.append("")

    # Subsections
    for subsection in section.subsections:
        lines.extend(_format_section_markdown(subsection, level + 1, include_sources))

    return lines


def _format_section_html(
    section: WikiSection,
    level: int,
    include_sources: bool,
) -> list[str]:
    """Format a section as HTML."""
    parts = []
    tag = f"h{min(level, 6)}"

    parts.append('<section class="section">')
    parts.append(f'<{tag}>{section.heading}</{tag}>')

    # Content paragraphs
    paragraphs = section.content.split("\n\n")
    for para in paragraphs:
        if para.strip():
            parts.append(f'<p>{para}</p>')

    # Source citations
    if include_sources and section.sources:
        source_refs = ", ".join(
            s.document_title or s.source_path for s in section.sources[:3]
        )
        parts.append(f'<p class="source">Sources: {source_refs}</p>')

    # Confidence indicator
    if section.confidence > 0:
        confidence_pct = int(section.confidence * 100)
        parts.append(f'<p class="confidence">Confidence: {confidence_pct}%</p>')

    # Subsections
    for subsection in section.subsections:
        parts.extend(_format_section_html(subsection, level + 1, include_sources))

    parts.append('</section>')
    return parts


def _format_section_plain(
    section: WikiSection,
    level: int,
    include_sources: bool,
) -> list[str]:
    """Format a section as plain text."""
    lines = []
    indent = "  " * level

    lines.append(f"{indent}{section.heading}")
    lines.append(f"{indent}{'-' * len(section.heading)}")
    lines.append("")

    # Indent content
    for line in section.content.split("\n"):
        lines.append(f"{indent}{line}")
    lines.append("")

    for subsection in section.subsections:
        lines.extend(_format_section_plain(subsection, level + 1, include_sources))

    return lines


def _format_citation(source: WikiSource) -> str:
    """Format a source as a citation string."""
    parts = []

    if source.document_title:
        parts.append(f'"{source.document_title}"')
    else:
        parts.append(source.source_path)

    if source.page_number:
        parts.append(f"p. {source.page_number}")

    if source.section:
        parts.append(f'Section: {source.section}')

    return ", ".join(parts)
