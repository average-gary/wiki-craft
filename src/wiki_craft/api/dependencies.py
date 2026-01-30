"""
FastAPI dependencies for Wiki-Craft.

Provides dependency injection for common services.
"""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from wiki_craft.storage.vector_store import VectorStore, get_vector_store


def get_store() -> VectorStore:
    """
    Dependency to get the vector store instance.

    Used by FastAPI's dependency injection system.
    """
    return get_vector_store()


# Type alias for dependency injection
StoreDep = Annotated[VectorStore, Depends(get_store)]
