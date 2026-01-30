"""
Wiki generation API routes.

Provides endpoints for generating wiki-style content from the knowledge base.
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from wiki_craft.api.dependencies import StoreDep
from wiki_craft.storage.models import (
    WikiEntry,
    WikiGenerateRequest,
    WikiGenerateResponse,
)
from wiki_craft.wiki.generator import WikiGenerator
from wiki_craft.wiki.formatter import WikiFormatter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/wiki/generate", response_model=WikiGenerateResponse)
async def generate_wiki_entry(
    store: StoreDep,
    request: WikiGenerateRequest,
) -> WikiGenerateResponse:
    """
    Generate a wiki entry for a topic or question.

    Searches the knowledge base and assembles relevant content
    with full source attribution.

    Args:
        request: WikiGenerateRequest with query and options

    Returns:
        WikiGenerateResponse with entry and formatted content
    """
    logger.info(f"Generating wiki for: {request.query}")

    generator = WikiGenerator(store)
    entry = generator.generate(
        query=request.query,
        max_sources=request.max_sources,
        include_sources=request.include_sources,
    )

    # Format output
    formatted = WikiFormatter.format(
        entry,
        format_type=request.output_format,
        include_sources=request.include_sources,
    )

    return WikiGenerateResponse(
        entry=entry,
        content=formatted,
        format=request.output_format,
    )


@router.get("/wiki/generate")
async def generate_wiki_entry_get(
    store: StoreDep,
    q: str = Query(..., description="Topic or question for wiki entry"),
    max_sources: int = Query(default=10, ge=1, le=50),
    format: str = Query(default="markdown", pattern="^(markdown|html|json|text)$"),
    include_sources: bool = Query(default=True),
) -> WikiGenerateResponse:
    """
    Generate a wiki entry (GET endpoint).

    Args:
        q: Topic or question
        max_sources: Maximum sources to use
        format: Output format (markdown, html, json, text)
        include_sources: Include source citations

    Returns:
        WikiGenerateResponse with formatted content
    """
    request = WikiGenerateRequest(
        query=q,
        max_sources=max_sources,
        output_format=format,
        include_sources=include_sources,
    )

    return await generate_wiki_entry(store, request)


@router.get("/wiki/sources/{entry_id}")
async def get_wiki_sources(
    store: StoreDep,
    entry_id: str,
) -> dict[str, Any]:
    """
    Get detailed source information for a wiki entry.

    Note: This requires the entry to have been cached/stored,
    which is not implemented in the basic version.
    For now, re-generate with the query.
    """
    # This would require caching wiki entries
    # For now, return a helpful message
    return {
        "message": "Source lookup requires entry caching. Use /wiki/generate with include_sources=true",
        "entry_id": entry_id,
    }


@router.post("/wiki/section")
async def generate_wiki_section(
    store: StoreDep,
    topic: str = Query(..., description="Section topic"),
    context: str | None = Query(default=None, description="Optional context"),
    max_sources: int = Query(default=5, ge=1, le=20),
) -> dict[str, Any]:
    """
    Generate a single wiki section.

    Useful for building custom wiki pages or expanding on specific topics.

    Args:
        topic: Section topic
        context: Optional context for better retrieval
        max_sources: Maximum sources

    Returns:
        Section content with sources
    """
    generator = WikiGenerator(store)
    section = generator.generate_section(
        topic=topic,
        context=context,
        max_sources=max_sources,
    )

    return {
        "heading": section.heading,
        "content": section.content,
        "confidence": section.confidence,
        "sources": [
            {
                "document_title": s.document_title,
                "source_path": s.source_path,
                "page_number": s.page_number,
                "section": s.section,
                "relevance_score": s.relevance_score,
                "excerpt": s.excerpt,
            }
            for s in section.sources
        ],
    }


@router.get("/wiki/topics")
async def suggest_topics(
    store: StoreDep,
    limit: int = Query(default=20, ge=1, le=100),
) -> dict[str, Any]:
    """
    Suggest wiki topics based on indexed content.

    Extracts unique topics from document sections and titles.

    Args:
        limit: Maximum topics to return

    Returns:
        List of suggested topics
    """
    documents = store.list_documents()

    topics = set()

    for doc in documents:
        # Add document titles as topics
        title = doc.get("document_title")
        if title:
            topics.add(title)

    # Get sections from documents
    for doc in documents[:10]:  # Limit to avoid too many lookups
        doc_id = doc.get("document_id")
        if doc_id:
            chunks = store.get_document_chunks(doc_id)
            for chunk in chunks:
                if chunk.metadata.section_hierarchy:
                    # Add leaf sections as potential topics
                    for section in chunk.metadata.section_hierarchy:
                        if len(section) > 5:  # Filter very short sections
                            topics.add(section)

    # Sort and limit
    topic_list = sorted(topics)[:limit]

    return {
        "topics": topic_list,
        "total": len(topics),
    }


@router.post("/wiki/compare")
async def compare_sources(
    store: StoreDep,
    query: str = Query(..., description="Topic to compare across sources"),
    max_per_source: int = Query(default=3, ge=1, le=10),
) -> dict[str, Any]:
    """
    Compare information about a topic across different sources.

    Useful for identifying agreement/disagreement between documents.

    Args:
        query: Topic to compare
        max_per_source: Maximum chunks per source document

    Returns:
        Content grouped by source document
    """
    from wiki_craft.storage.models import SearchQuery

    # Search for content
    search_query = SearchQuery(query=query, limit=50, min_score=0.3)
    results = store.search(search_query)

    # Group by document
    by_document: dict[str, dict[str, Any]] = {}

    for result in results.results:
        doc_id = result.metadata.document_id
        doc_title = result.metadata.document_title or result.metadata.source_path

        if doc_id not in by_document:
            by_document[doc_id] = {
                "document_id": doc_id,
                "document_title": doc_title,
                "source_path": result.metadata.source_path,
                "excerpts": [],
            }

        if len(by_document[doc_id]["excerpts"]) < max_per_source:
            by_document[doc_id]["excerpts"].append({
                "text": result.text,
                "score": result.score,
                "page_number": result.metadata.page_number,
                "section": " > ".join(result.metadata.section_hierarchy) if result.metadata.section_hierarchy else None,
            })

    return {
        "query": query,
        "sources": list(by_document.values()),
        "source_count": len(by_document),
    }
