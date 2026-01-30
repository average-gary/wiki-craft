"""
FastAPI application factory and configuration.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from wiki_craft import __version__
from wiki_craft.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup
    logger.info(f"Starting Wiki-Craft v{__version__}")
    settings.ensure_directories()

    yield

    # Shutdown
    logger.info("Shutting down Wiki-Craft")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title=settings.app_name,
        description=(
            "Document ingestion and indexing system for building "
            "wiki-style knowledge bases with full source tracking."
        ),
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure as needed
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    from wiki_craft.api.routes import documents, ingest, search, wiki

    app.include_router(ingest.router, prefix=settings.api_prefix, tags=["Ingest"])
    app.include_router(search.router, prefix=settings.api_prefix, tags=["Search"])
    app.include_router(documents.router, prefix=settings.api_prefix, tags=["Documents"])
    app.include_router(wiki.router, prefix=settings.api_prefix, tags=["Wiki"])

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "version": __version__}

    @app.get("/")
    async def root():
        """Root endpoint with API info."""
        return {
            "name": settings.app_name,
            "version": __version__,
            "docs": "/docs",
            "api_prefix": settings.api_prefix,
        }

    return app


# Default app instance
app = create_app()
