"""FastAPI application and routes for Wiki-Craft."""

from wiki_craft.api.dependencies import get_store
from wiki_craft.api.app import create_app, app

__all__ = [
    "create_app",
    "app",
    "get_store",
]
