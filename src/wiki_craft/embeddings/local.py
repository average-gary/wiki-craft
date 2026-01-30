"""
Local embedding generation using sentence-transformers.

Provides high-quality embeddings without external API calls.
"""

import logging
from typing import ClassVar

from wiki_craft.config import settings

logger = logging.getLogger(__name__)


class LocalEmbedder:
    """
    Generates embeddings using sentence-transformers models.

    Default model: all-mpnet-base-v2 (768 dimensions, high quality)
    Alternative: all-MiniLM-L6-v2 (384 dimensions, faster)

    The embedder is designed to be reused - model loading is expensive.
    """

    _instance: ClassVar["LocalEmbedder | None"] = None
    _model = None

    def __init__(
        self,
        model_name: str | None = None,
        device: str | None = None,
    ) -> None:
        """
        Initialize the embedder.

        Args:
            model_name: Name of the sentence-transformers model
            device: Device to run on ('cpu', 'cuda', 'mps')
        """
        self.model_name = model_name or settings.embedding_model
        self.device = device or settings.embedding_device
        self.batch_size = settings.embedding_batch_size
        self._model = None

    @property
    def model(self):
        """Lazy load the model on first use."""
        if self._model is None:
            self._load_model()
        return self._model

    def _load_model(self) -> None:
        """Load the sentence-transformers model."""
        from sentence_transformers import SentenceTransformer

        logger.info(f"Loading embedding model: {self.model_name} on {self.device}")
        self._model = SentenceTransformer(self.model_name, device=self.device)
        logger.info(f"Model loaded. Embedding dimension: {self.dimension}")

    @property
    def dimension(self) -> int:
        """Get the embedding dimension for the loaded model."""
        return self.model.get_sentence_embedding_dimension()

    def embed(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return embedding.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts efficiently.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        logger.debug(f"Embedding batch of {len(texts)} texts")

        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            convert_to_numpy=True,
            show_progress_bar=len(texts) > 100,
        )

        return [emb.tolist() for emb in embeddings]

    def embed_query(self, query: str) -> list[float]:
        """
        Generate embedding for a search query.

        Some models benefit from different encoding for queries vs documents.
        This method can be overridden for such models.

        Args:
            query: Search query text

        Returns:
            Query embedding vector
        """
        return self.embed(query)

    @classmethod
    def get_instance(cls) -> "LocalEmbedder":
        """
        Get the singleton embedder instance.

        Reuses the same model across the application.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (useful for testing)."""
        cls._instance = None


def get_embedder() -> LocalEmbedder:
    """
    Get the global embedder instance.

    Returns:
        LocalEmbedder singleton instance
    """
    return LocalEmbedder.get_instance()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Convenience function to embed multiple texts.

    Args:
        texts: Texts to embed

    Returns:
        List of embedding vectors
    """
    embedder = get_embedder()
    return embedder.embed_batch(texts)


def embed_text(text: str) -> list[float]:
    """
    Convenience function to embed a single text.

    Args:
        text: Text to embed

    Returns:
        Embedding vector
    """
    embedder = get_embedder()
    return embedder.embed(text)
