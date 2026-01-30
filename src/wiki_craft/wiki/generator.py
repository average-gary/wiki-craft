"""
Wiki content generator with source attribution.

Generates wiki-style entries from search results with full citations.
"""

import logging
from typing import Any

from wiki_craft.config import settings
from wiki_craft.storage.models import (
    SearchQuery,
    SearchResult,
    WikiEntry,
    WikiSection,
    WikiSource,
)
from wiki_craft.storage.vector_store import VectorStore

logger = logging.getLogger(__name__)


class WikiGenerator:
    """
    Generates wiki entries from document knowledge base.

    Features:
    - Query-based content retrieval
    - Automatic source attribution
    - Structured output with sections
    - Multiple output formats
    """

    def __init__(self, store: VectorStore) -> None:
        """
        Initialize the generator.

        Args:
            store: Vector store for content retrieval
        """
        self.store = store
        self.max_sources_per_section = settings.max_sources_per_section

    def generate(
        self,
        query: str,
        max_sources: int = 10,
        include_sources: bool = True,
    ) -> WikiEntry:
        """
        Generate a wiki entry for a query.

        Args:
            query: Topic or question for the wiki entry
            max_sources: Maximum number of source chunks to use
            include_sources: Whether to include source citations

        Returns:
            WikiEntry with content and sources
        """
        logger.info(f"Generating wiki entry for: {query}")

        # Search for relevant content
        search_query = SearchQuery(query=query, limit=max_sources, min_score=0.3)
        search_response = self.store.search(search_query)

        if not search_response.results:
            logger.warning(f"No results found for query: {query}")
            return WikiEntry(
                title=self._generate_title(query),
                summary="No relevant information found in the knowledge base.",
                query=query,
            )

        # Group results by document/section
        grouped = self._group_results(search_response.results)

        # Build wiki entry
        entry = self._build_entry(query, grouped, include_sources)

        logger.info(
            f"Generated wiki entry with {len(entry.sections)} sections, "
            f"{len(entry.all_sources)} sources"
        )

        return entry

    def generate_section(
        self,
        topic: str,
        context: str | None = None,
        max_sources: int = 5,
    ) -> WikiSection:
        """
        Generate a single wiki section.

        Args:
            topic: Section topic
            context: Optional context for better retrieval
            max_sources: Maximum sources for this section

        Returns:
            WikiSection with content and sources
        """
        # Combine topic with context for better search
        search_text = f"{context} {topic}" if context else topic

        search_query = SearchQuery(query=search_text, limit=max_sources, min_score=0.3)
        results = self.store.search(search_query).results

        if not results:
            return WikiSection(
                heading=topic,
                content="No information available.",
                confidence=0.0,
            )

        # Build section content
        content = self._synthesize_content(results)
        sources = self._results_to_sources(results)

        # Calculate confidence based on source scores
        avg_score = sum(r.score for r in results) / len(results)

        return WikiSection(
            heading=topic,
            content=content,
            sources=sources,
            confidence=avg_score,
        )

    def _group_results(
        self, results: list[SearchResult]
    ) -> dict[str, list[SearchResult]]:
        """
        Group search results by document and section.

        Returns dict mapping section keys to results.
        """
        grouped: dict[str, list[SearchResult]] = {}

        for result in results:
            # Create key from document and section
            section_path = " > ".join(result.metadata.section_hierarchy) if result.metadata.section_hierarchy else "General"
            key = f"{result.metadata.document_title or 'Untitled'}: {section_path}"

            if key not in grouped:
                grouped[key] = []
            grouped[key].append(result)

        return grouped

    def _build_entry(
        self,
        query: str,
        grouped_results: dict[str, list[SearchResult]],
        include_sources: bool,
    ) -> WikiEntry:
        """Build a WikiEntry from grouped results."""
        title = self._generate_title(query)

        # Generate summary from top results
        all_results = []
        for results in grouped_results.values():
            all_results.extend(results)
        all_results.sort(key=lambda r: r.score, reverse=True)

        summary = self._generate_summary(all_results[:3])

        # Build sections from grouped results
        sections = []
        all_sources = []

        for section_key, results in grouped_results.items():
            # Use the section hierarchy as heading
            if ": " in section_key:
                heading = section_key.split(": ", 1)[1]
            else:
                heading = section_key

            content = self._synthesize_content(results)
            sources = self._results_to_sources(results) if include_sources else []

            # Calculate confidence
            avg_score = sum(r.score for r in results) / len(results)

            sections.append(
                WikiSection(
                    heading=heading,
                    content=content,
                    sources=sources,
                    confidence=avg_score,
                )
            )

            all_sources.extend(sources)

        # Sort sections by confidence
        sections.sort(key=lambda s: s.confidence, reverse=True)

        # Deduplicate sources
        unique_sources = self._deduplicate_sources(all_sources)

        return WikiEntry(
            title=title,
            summary=summary,
            sections=sections,
            all_sources=unique_sources,
            query=query,
        )

    def _generate_title(self, query: str) -> str:
        """Generate a wiki-style title from query."""
        # Capitalize and clean up
        title = query.strip()

        # Remove question marks and common prefixes
        title = title.rstrip("?")
        for prefix in ["what is ", "how to ", "why ", "when ", "where ", "who "]:
            if title.lower().startswith(prefix):
                title = title[len(prefix) :]
                break

        # Title case
        return title.title()

    def _generate_summary(self, top_results: list[SearchResult]) -> str:
        """Generate a summary from top search results."""
        if not top_results:
            return ""

        # Take excerpts from top results
        excerpts = []
        for result in top_results[:3]:
            text = result.text.strip()
            # Take first sentence or first 200 chars
            if ". " in text[:200]:
                excerpt = text[: text.find(". ", 0, 200) + 1]
            else:
                excerpt = text[:200] + "..." if len(text) > 200 else text
            excerpts.append(excerpt)

        return " ".join(excerpts)

    def _synthesize_content(self, results: list[SearchResult]) -> str:
        """
        Synthesize coherent content from search results.

        This is a simple version that concatenates results.
        A more sophisticated version could use an LLM for synthesis.
        """
        if not results:
            return ""

        # Sort by position in document if from same doc
        results.sort(key=lambda r: (r.metadata.document_id, r.metadata.chunk_index))

        # Combine texts, avoiding duplicates
        seen_texts = set()
        paragraphs = []

        for result in results:
            # Normalize for dedup
            normalized = result.text.strip().lower()[:100]
            if normalized in seen_texts:
                continue
            seen_texts.add(normalized)

            paragraphs.append(result.text.strip())

        return "\n\n".join(paragraphs)

    def _results_to_sources(self, results: list[SearchResult]) -> list[WikiSource]:
        """Convert search results to wiki sources."""
        sources = []

        for result in results:
            section = " > ".join(result.metadata.section_hierarchy) if result.metadata.section_hierarchy else None

            sources.append(
                WikiSource(
                    chunk_id=result.chunk_id,
                    document_id=result.metadata.document_id,
                    document_title=result.metadata.document_title,
                    source_path=result.metadata.source_path,
                    page_number=result.metadata.page_number,
                    section=section,
                    relevance_score=result.score,
                    excerpt=result.text[:200] + "..." if len(result.text) > 200 else result.text,
                )
            )

        return sources

    def _deduplicate_sources(self, sources: list[WikiSource]) -> list[WikiSource]:
        """Remove duplicate sources, keeping highest relevance."""
        seen = {}

        for source in sources:
            key = (source.document_id, source.page_number, source.section)
            if key not in seen or source.relevance_score > seen[key].relevance_score:
                seen[key] = source

        # Sort by relevance
        unique = list(seen.values())
        unique.sort(key=lambda s: s.relevance_score, reverse=True)

        return unique


def generate_wiki_entry(
    store: VectorStore,
    query: str,
    max_sources: int = 10,
    include_sources: bool = True,
) -> WikiEntry:
    """
    Convenience function to generate a wiki entry.

    Args:
        store: Vector store instance
        query: Topic or question
        max_sources: Maximum sources to use
        include_sources: Include source citations

    Returns:
        Generated WikiEntry
    """
    generator = WikiGenerator(store)
    return generator.generate(query, max_sources, include_sources)
