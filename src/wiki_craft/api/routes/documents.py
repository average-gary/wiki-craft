"""
Document management API routes.

Provides CRUD operations for documents and their metadata.
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status

from wiki_craft.api.dependencies import StoreDep
from wiki_craft.storage.models import DocumentMetadata, StoredChunk

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/documents")
async def list_documents(
    store: StoreDep,
    offset: int = 0,
    limit: int = 50,
) -> dict[str, Any]:
    """
    List all ingested documents.

    Args:
        offset: Pagination offset
        limit: Maximum documents to return

    Returns:
        Paginated list of documents with metadata
    """
    all_docs = store.list_documents()

    # Apply pagination
    total = len(all_docs)
    docs = all_docs[offset : offset + limit]

    return {
        "documents": docs,
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@router.get("/documents/{document_id}")
async def get_document(
    store: StoreDep,
    document_id: str,
) -> dict[str, Any]:
    """
    Get document details and metadata.

    Args:
        document_id: Document ID

    Returns:
        Document metadata and chunk summary
    """
    chunks = store.get_document_chunks(document_id)

    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}",
        )

    # Get metadata from first chunk
    first_chunk = chunks[0]
    metadata = first_chunk.metadata

    return {
        "document_id": document_id,
        "source_path": metadata.source_path,
        "document_title": metadata.document_title,
        "document_type": metadata.document_type.value,
        "total_chunks": len(chunks),
        "ingested_at": metadata.ingested_at.isoformat(),
        "sections": _extract_sections(chunks),
    }


@router.get("/documents/{document_id}/chunks")
async def get_document_chunks(
    store: StoreDep,
    document_id: str,
    offset: int = 0,
    limit: int = 50,
) -> dict[str, Any]:
    """
    Get all chunks for a document.

    Args:
        document_id: Document ID
        offset: Pagination offset
        limit: Maximum chunks to return

    Returns:
        Paginated list of chunks
    """
    chunks = store.get_document_chunks(document_id)

    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}",
        )

    total = len(chunks)
    paginated = chunks[offset : offset + limit]

    return {
        "document_id": document_id,
        "chunks": [
            {
                "chunk_id": c.chunk_id,
                "text": c.text,
                "chunk_index": c.metadata.chunk_index,
                "page_number": c.metadata.page_number,
                "section": " > ".join(c.metadata.section_hierarchy)
                if c.metadata.section_hierarchy
                else None,
            }
            for c in paginated
        ],
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@router.delete("/documents/{document_id}")
async def delete_document(
    store: StoreDep,
    document_id: str,
) -> dict[str, Any]:
    """
    Delete a document and all its chunks.

    Args:
        document_id: Document ID to delete

    Returns:
        Confirmation with chunk count deleted
    """
    deleted_count = store.delete_document(document_id)

    if deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}",
        )

    logger.info(f"Deleted document {document_id} ({deleted_count} chunks)")

    return {
        "status": "deleted",
        "document_id": document_id,
        "chunks_deleted": deleted_count,
    }


@router.get("/documents/{document_id}/text")
async def get_document_text(
    store: StoreDep,
    document_id: str,
) -> dict[str, Any]:
    """
    Get the full reconstructed text of a document.

    Args:
        document_id: Document ID

    Returns:
        Full document text and metadata
    """
    chunks = store.get_document_chunks(document_id)

    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}",
        )

    # Reconstruct text from chunks
    full_text = "\n\n".join(c.text for c in chunks)
    metadata = chunks[0].metadata

    return {
        "document_id": document_id,
        "document_title": metadata.document_title,
        "text": full_text,
        "word_count": len(full_text.split()),
        "chunk_count": len(chunks),
    }


@router.get("/chunks/{chunk_id}")
async def get_chunk(
    store: StoreDep,
    chunk_id: str,
) -> dict[str, Any]:
    """
    Get a specific chunk by ID.

    Args:
        chunk_id: Chunk ID

    Returns:
        Chunk content and metadata
    """
    chunk = store.get_chunk(chunk_id)

    if not chunk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chunk not found: {chunk_id}",
        )

    return {
        "chunk_id": chunk.chunk_id,
        "text": chunk.text,
        "metadata": {
            "document_id": chunk.metadata.document_id,
            "document_title": chunk.metadata.document_title,
            "source_path": chunk.metadata.source_path,
            "page_number": chunk.metadata.page_number,
            "section_hierarchy": chunk.metadata.section_hierarchy,
            "chunk_index": chunk.metadata.chunk_index,
            "total_chunks": chunk.metadata.total_chunks,
            "content_type": chunk.metadata.content_type.value,
        },
    }


@router.get("/stats")
async def get_stats(store: StoreDep) -> dict[str, Any]:
    """
    Get statistics about the knowledge base.

    Returns:
        Stats including document count, chunk count, etc.
    """
    documents = store.list_documents()

    # Calculate stats
    total_chunks = store.count
    doc_types = {}
    for doc in documents:
        doc_type = doc.get("document_type", "unknown")
        doc_types[doc_type] = doc_types.get(doc_type, 0) + 1

    return {
        "total_documents": len(documents),
        "total_chunks": total_chunks,
        "documents_by_type": doc_types,
        "avg_chunks_per_document": total_chunks / len(documents) if documents else 0,
    }


def _extract_sections(chunks: list[StoredChunk]) -> list[dict[str, Any]]:
    """Extract unique sections from document chunks."""
    sections = []
    seen = set()

    for chunk in chunks:
        if chunk.metadata.section_hierarchy:
            key = "|".join(chunk.metadata.section_hierarchy)
            if key not in seen:
                seen.add(key)
                sections.append({
                    "hierarchy": chunk.metadata.section_hierarchy,
                    "page_number": chunk.metadata.page_number,
                })

    return sections
