"""
ChromaDB vector store integration.

Provides persistent storage and retrieval of document chunks with embeddings.
"""

import logging
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from wiki_craft.config import settings
from wiki_craft.embeddings.local import get_embedder
from wiki_craft.storage.models import (
    ChunkMetadata,
    DocumentType,
    SearchQuery,
    SearchResponse,
    SearchResult,
    StoredChunk,
)

logger = logging.getLogger(__name__)


class VectorStore:
    """
    ChromaDB-backed vector store for document chunks.

    Features:
    - Persistent local storage
    - Semantic search with metadata filtering
    - Batch operations for efficiency
    - Document-level management
    """

    _instance: "VectorStore | None" = None

    def __init__(
        self,
        persist_directory: str | None = None,
        collection_name: str | None = None,
    ) -> None:
        """
        Initialize the vector store.

        Args:
            persist_directory: Directory for persistent storage
            collection_name: Name of the ChromaDB collection
        """
        self.persist_directory = persist_directory or str(settings.chromadb_dir)
        self.collection_name = collection_name or settings.chroma_collection_name

        # Ensure directory exists
        settings.ensure_directories()

        # Initialize ChromaDB client
        self._client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        # Get or create collection
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Wiki-Craft document chunks"},
        )

        # Get embedder
        self._embedder = get_embedder()

        logger.info(
            f"VectorStore initialized: {self.collection_name} "
            f"({self._collection.count()} chunks)"
        )

    @property
    def count(self) -> int:
        """Get total number of chunks in the store."""
        return self._collection.count()

    def add_chunks(self, chunks: list[StoredChunk]) -> list[str]:
        """
        Add chunks to the vector store.

        Generates embeddings if not present and stores with metadata.

        Args:
            chunks: List of chunks to add

        Returns:
            List of chunk IDs
        """
        if not chunks:
            return []

        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []
        embeddings = []

        # Generate embeddings for chunks without them
        texts_to_embed = []
        chunks_needing_embeddings = []

        for chunk in chunks:
            ids.append(chunk.chunk_id)
            documents.append(chunk.text)
            metadatas.append(chunk.metadata.to_chroma_metadata())

            if chunk.embedding:
                embeddings.append(chunk.embedding)
            else:
                texts_to_embed.append(chunk.text)
                chunks_needing_embeddings.append(len(embeddings))
                embeddings.append(None)  # Placeholder

        # Batch embed texts
        if texts_to_embed:
            logger.debug(f"Generating embeddings for {len(texts_to_embed)} chunks")
            new_embeddings = self._embedder.embed_batch(texts_to_embed)
            for i, idx in enumerate(chunks_needing_embeddings):
                embeddings[idx] = new_embeddings[i]

        # Add to ChromaDB
        self._collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )

        logger.info(f"Added {len(chunks)} chunks to vector store")
        return ids

    def search(self, query: SearchQuery) -> SearchResponse:
        """
        Perform semantic search.

        Args:
            query: Search query with parameters

        Returns:
            SearchResponse with results
        """
        import time

        start_time = time.time()

        # Generate query embedding
        query_embedding = self._embedder.embed_query(query.query)

        # Build where filter
        where_filter = self._build_where_filter(query)

        # Execute search
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=query.limit,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        # Convert to SearchResults
        search_results = []
        if results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                # ChromaDB returns distances, convert to similarity score
                distance = results["distances"][0][i] if results["distances"] else 0
                # Cosine distance to similarity: 1 - distance (for L2, use different formula)
                score = max(0, 1 - distance)

                if score < query.min_score:
                    continue

                metadata = ChunkMetadata.from_chroma_metadata(results["metadatas"][0][i])

                search_results.append(
                    SearchResult(
                        chunk_id=chunk_id,
                        text=results["documents"][0][i],
                        score=score,
                        metadata=metadata,
                    )
                )

        search_time = (time.time() - start_time) * 1000

        return SearchResponse(
            query=query.query,
            results=search_results,
            total_results=len(search_results),
            search_time_ms=search_time,
        )

    def search_similar(self, chunk_id: str, limit: int = 10) -> list[SearchResult]:
        """
        Find chunks similar to a given chunk.

        Args:
            chunk_id: ID of the reference chunk
            limit: Maximum results

        Returns:
            List of similar chunks
        """
        # Get the chunk's embedding
        result = self._collection.get(ids=[chunk_id], include=["embeddings"])
        if not result["embeddings"]:
            return []

        embedding = result["embeddings"][0]

        # Search with that embedding
        results = self._collection.query(
            query_embeddings=[embedding],
            n_results=limit + 1,  # +1 to exclude self
            include=["documents", "metadatas", "distances"],
        )

        search_results = []
        if results["ids"] and results["ids"][0]:
            for i, cid in enumerate(results["ids"][0]):
                if cid == chunk_id:  # Skip self
                    continue

                distance = results["distances"][0][i] if results["distances"] else 0
                score = max(0, 1 - distance)
                metadata = ChunkMetadata.from_chroma_metadata(results["metadatas"][0][i])

                search_results.append(
                    SearchResult(
                        chunk_id=cid,
                        text=results["documents"][0][i],
                        score=score,
                        metadata=metadata,
                    )
                )

        return search_results[:limit]

    def get_chunk(self, chunk_id: str) -> StoredChunk | None:
        """
        Retrieve a specific chunk by ID.

        Args:
            chunk_id: Chunk ID

        Returns:
            StoredChunk or None if not found
        """
        result = self._collection.get(
            ids=[chunk_id],
            include=["documents", "metadatas", "embeddings"],
        )

        if not result["ids"]:
            return None

        return StoredChunk(
            chunk_id=chunk_id,
            text=result["documents"][0],
            metadata=ChunkMetadata.from_chroma_metadata(result["metadatas"][0]),
            embedding=result["embeddings"][0] if result["embeddings"] else None,
        )

    def get_document_chunks(self, document_id: str) -> list[StoredChunk]:
        """
        Get all chunks for a document.

        Args:
            document_id: Document ID

        Returns:
            List of chunks ordered by chunk_index
        """
        results = self._collection.get(
            where={"document_id": document_id},
            include=["documents", "metadatas"],
        )

        chunks = []
        if results["ids"]:
            for i, chunk_id in enumerate(results["ids"]):
                chunks.append(
                    StoredChunk(
                        chunk_id=chunk_id,
                        text=results["documents"][i],
                        metadata=ChunkMetadata.from_chroma_metadata(results["metadatas"][i]),
                    )
                )

        # Sort by chunk_index
        chunks.sort(key=lambda c: c.metadata.chunk_index)
        return chunks

    def delete_document(self, document_id: str) -> int:
        """
        Delete all chunks for a document.

        Args:
            document_id: Document ID to delete

        Returns:
            Number of chunks deleted
        """
        # Get chunk IDs for document
        results = self._collection.get(
            where={"document_id": document_id},
            include=[],
        )

        if not results["ids"]:
            return 0

        count = len(results["ids"])
        self._collection.delete(ids=results["ids"])

        logger.info(f"Deleted {count} chunks for document {document_id}")
        return count

    def delete_chunks(self, chunk_ids: list[str]) -> int:
        """
        Delete specific chunks.

        Args:
            chunk_ids: List of chunk IDs to delete

        Returns:
            Number of chunks deleted
        """
        if not chunk_ids:
            return 0

        self._collection.delete(ids=chunk_ids)
        return len(chunk_ids)

    def list_documents(self) -> list[dict[str, Any]]:
        """
        List all unique documents in the store.

        Returns:
            List of document info dicts
        """
        # Get all metadata
        results = self._collection.get(include=["metadatas"])

        # Extract unique documents
        documents = {}
        for metadata in results["metadatas"]:
            doc_id = metadata["document_id"]
            if doc_id not in documents:
                documents[doc_id] = {
                    "document_id": doc_id,
                    "source_path": metadata["source_path"],
                    "document_title": metadata.get("document_title"),
                    "document_type": metadata.get("document_type"),
                    "total_chunks": metadata.get("total_chunks", 0),
                    "ingested_at": metadata.get("ingested_at"),
                }

        return list(documents.values())

    def _build_where_filter(self, query: SearchQuery) -> dict[str, Any] | None:
        """Build ChromaDB where filter from query parameters."""
        conditions = []

        if query.document_ids:
            if len(query.document_ids) == 1:
                conditions.append({"document_id": query.document_ids[0]})
            else:
                conditions.append({"document_id": {"$in": query.document_ids}})

        if query.document_types:
            type_values = [dt.value for dt in query.document_types]
            if len(type_values) == 1:
                conditions.append({"document_type": type_values[0]})
            else:
                conditions.append({"document_type": {"$in": type_values}})

        if not conditions:
            return None
        elif len(conditions) == 1:
            return conditions[0]
        else:
            return {"$and": conditions}

    @classmethod
    def get_instance(cls) -> "VectorStore":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (for testing)."""
        cls._instance = None


def get_vector_store() -> VectorStore:
    """Get the global vector store instance."""
    return VectorStore.get_instance()
