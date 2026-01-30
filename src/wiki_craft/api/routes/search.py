"""
Search API routes.

Provides semantic search across ingested documents.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Query

from wiki_craft.api.dependencies import StoreDep
from wiki_craft.storage.models import (
    DocumentType,
    SearchQuery,
    SearchResponse,
    SearchResult,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search(
    store: StoreDep,
    query: SearchQuery,
) -> SearchResponse:
    """
    Perform semantic search across documents.

    Args:
        query: Search query with optional filters

    Returns:
        SearchResponse with ranked results and metadata
    """
    logger.debug(f"Search query: {query.query}")
    response = store.search(query)
    logger.info(
        f"Search '{query.query[:50]}...' returned {response.total_results} results "
        f"in {response.search_time_ms:.2f}ms"
    )
    return response


@router.get("/search", response_model=SearchResponse)
async def search_get(
    store: StoreDep,
    q: Annotated[str, Query(description="Search query text")],
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    min_score: Annotated[float, Query(ge=0, le=1)] = 0.0,
    document_type: Annotated[list[DocumentType] | None, Query()] = None,
) -> SearchResponse:
    """
    Perform semantic search (GET endpoint for convenience).

    Args:
        q: Search query text
        limit: Maximum results (default 10)
        min_score: Minimum relevance score (0-1)
        document_type: Filter by document types

    Returns:
        SearchResponse with ranked results
    """
    query = SearchQuery(
        query=q,
        limit=limit,
        min_score=min_score,
        document_types=document_type,
    )
    return store.search(query)


@router.get("/search/similar/{chunk_id}", response_model=list[SearchResult])
async def search_similar(
    store: StoreDep,
    chunk_id: str,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> list[SearchResult]:
    """
    Find chunks similar to a given chunk.

    Useful for finding related content or expanding on a topic.

    Args:
        chunk_id: ID of the reference chunk
        limit: Maximum results

    Returns:
        List of similar chunks with scores
    """
    results = store.search_similar(chunk_id, limit=limit)
    return results


@router.get("/search/context/{chunk_id}")
async def get_chunk_context(
    store: StoreDep,
    chunk_id: str,
    window: Annotated[int, Query(ge=1, le=10)] = 2,
) -> dict:
    """
    Get a chunk with surrounding context.

    Returns the chunk and neighboring chunks from the same document.

    Args:
        chunk_id: ID of the target chunk
        window: Number of chunks before/after to include

    Returns:
        Dict with target chunk and context chunks
    """
    # Get the target chunk
    target = store.get_chunk(chunk_id)
    if not target:
        return {"error": "Chunk not found"}

    # Get all chunks from the same document
    doc_chunks = store.get_document_chunks(target.metadata.document_id)

    # Find target position and extract window
    target_idx = target.metadata.chunk_index
    start_idx = max(0, target_idx - window)
    end_idx = min(len(doc_chunks), target_idx + window + 1)

    context_chunks = doc_chunks[start_idx:end_idx]

    return {
        "target_chunk": {
            "id": target.chunk_id,
            "text": target.text,
            "index": target_idx,
        },
        "context": [
            {
                "id": c.chunk_id,
                "text": c.text,
                "index": c.metadata.chunk_index,
                "is_target": c.chunk_id == chunk_id,
            }
            for c in context_chunks
        ],
        "document_id": target.metadata.document_id,
        "document_title": target.metadata.document_title,
    }
