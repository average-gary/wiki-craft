"""
Document ingestion API routes.

Handles file uploads and URL ingestion.
"""

import logging
import tempfile
from pathlib import Path
from typing import Any

import aiofiles
import httpx
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from wiki_craft.api.dependencies import StoreDep
from wiki_craft.parsers import ParserRegistry
from wiki_craft.processing.chunker import chunk_document
from wiki_craft.processing.metadata import enrich_document
from wiki_craft.storage.models import (
    DocumentType,
    IngestRequest,
    IngestResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ingest/file", response_model=IngestResponse)
async def ingest_file(
    store: StoreDep,
    file: UploadFile = File(...),
    custom_metadata: str | None = Form(default=None),
) -> IngestResponse:
    """
    Ingest a document from file upload.

    Supports: PDF, Word (.docx), Excel (.xlsx), Markdown, HTML, EPUB, plain text.

    Args:
        file: The uploaded file
        custom_metadata: Optional JSON string of custom metadata

    Returns:
        IngestResponse with document ID and chunk count
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    file_path = Path(file.filename)

    # Get appropriate parser
    parser = ParserRegistry.get_parser(file_path, file.content_type)
    if not parser:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file_path.suffix}",
        )

    # Save to temp file (some parsers need file path)
    with tempfile.NamedTemporaryFile(
        suffix=file_path.suffix, delete=False
    ) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        # Parse document
        logger.info(f"Parsing document: {file.filename}")
        document = parser.parse(tmp_path)
        document.metadata.source_path = file.filename
        document.metadata.filename = file.filename

        # Parse custom metadata if provided
        metadata_dict: dict[str, Any] = {}
        if custom_metadata:
            import json
            try:
                metadata_dict = json.loads(custom_metadata)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid JSON in custom_metadata",
                )

        # Enrich metadata
        document = enrich_document(document, metadata_dict)

        # Chunk document
        chunks = chunk_document(document)

        # Store chunks
        chunk_ids = store.add_chunks(chunks)

        logger.info(
            f"Ingested {file.filename}: {len(chunk_ids)} chunks, "
            f"doc_id={document.metadata.document_id}"
        )

        return IngestResponse(
            document_id=document.metadata.document_id,
            filename=file.filename,
            document_type=document.metadata.document_type,
            chunks_created=len(chunk_ids),
            errors=document.parsing_errors,
        )

    except Exception as e:
        logger.error(f"Failed to ingest {file.filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}",
        )
    finally:
        # Clean up temp file
        tmp_path.unlink(missing_ok=True)


@router.post("/ingest/batch", response_model=list[IngestResponse])
async def ingest_batch(
    store: StoreDep,
    files: list[UploadFile] = File(...),
) -> list[IngestResponse]:
    """
    Ingest multiple documents at once.

    Args:
        files: List of files to ingest

    Returns:
        List of IngestResponse for each file
    """
    results = []

    for file in files:
        try:
            # Reuse single file ingest
            result = await ingest_file(store, file)
            results.append(result)
        except HTTPException as e:
            # Record error but continue
            results.append(
                IngestResponse(
                    document_id="",
                    filename=file.filename or "unknown",
                    document_type=DocumentType.UNKNOWN,
                    chunks_created=0,
                    status="error",
                    errors=[str(e.detail)],
                )
            )

    return results


@router.post("/ingest/url", response_model=IngestResponse)
async def ingest_url(
    store: StoreDep,
    request: IngestRequest,
) -> IngestResponse:
    """
    Ingest a document from URL.

    Downloads the content and processes it based on content type.

    Args:
        request: IngestRequest with URL and optional metadata

    Returns:
        IngestResponse with document ID and chunk count
    """
    url = request.url

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
            response = await client.get(url)
            response.raise_for_status()

            content = response.content
            content_type = response.headers.get("content-type", "")

            # Determine filename from URL or content-disposition
            filename = _extract_filename(url, response.headers)
            file_path = Path(filename)

            # Get parser
            parser = ParserRegistry.get_parser(file_path, content_type)
            if not parser:
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail=f"Unsupported content type: {content_type}",
                )

            # Save to temp file
            with tempfile.NamedTemporaryFile(
                suffix=file_path.suffix, delete=False
            ) as tmp:
                tmp.write(content)
                tmp_path = Path(tmp.name)

            try:
                # Parse document
                document = parser.parse(tmp_path)
                document.metadata.source_path = url
                document.metadata.filename = filename

                # Enrich with custom metadata
                document = enrich_document(document, request.custom_metadata)

                # Chunk and store
                chunks = chunk_document(document)
                chunk_ids = store.add_chunks(chunks)

                return IngestResponse(
                    document_id=document.metadata.document_id,
                    filename=filename,
                    document_type=document.metadata.document_type,
                    chunks_created=len(chunk_ids),
                    errors=document.parsing_errors,
                )

            finally:
                tmp_path.unlink(missing_ok=True)

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch URL: {str(e)}",
        )


def _extract_filename(url: str, headers: dict) -> str:
    """Extract filename from URL or Content-Disposition header."""
    from urllib.parse import unquote, urlparse

    # Try Content-Disposition
    cd = headers.get("content-disposition", "")
    if "filename=" in cd:
        import re
        match = re.search(r'filename[*]?=["\']?([^"\';]+)', cd)
        if match:
            return unquote(match.group(1))

    # Fall back to URL path
    parsed = urlparse(url)
    path = parsed.path
    if path:
        filename = path.split("/")[-1]
        if filename:
            return unquote(filename)

    # Default based on content type
    content_type = headers.get("content-type", "")
    if "html" in content_type:
        return "page.html"
    elif "pdf" in content_type:
        return "document.pdf"

    return "document.txt"
