"""
FastAPI application factory and configuration.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from wiki_craft import __version__
from wiki_craft.config import settings

logger = logging.getLogger(__name__)

# Path to frontend build directory
FRONTEND_DIR = Path(__file__).parent.parent.parent.parent / "frontend" / "dist"


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

    # Serve frontend static files if the build exists
    if FRONTEND_DIR.exists():
        # Mount static assets (JS, CSS, images)
        assets_dir = FRONTEND_DIR / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

        @app.get("/")
        async def serve_spa_root():
            """Serve the SPA index.html at root."""
            return FileResponse(FRONTEND_DIR / "index.html")

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            """
            Serve static files or fall back to index.html for SPA routing.
            This must be registered last to not interfere with API routes.
            """
            # Check if it's a static file that exists
            file_path = FRONTEND_DIR / full_path
            if file_path.exists() and file_path.is_file():
                return FileResponse(file_path)

            # Fall back to index.html for SPA client-side routing
            return FileResponse(FRONTEND_DIR / "index.html")

        logger.info(f"Serving frontend from {FRONTEND_DIR}")
    else:
        # No frontend build, serve API info at root
        @app.get("/")
        async def root():
            """Root endpoint with API info."""
            return {
                "name": settings.app_name,
                "version": __version__,
                "docs": "/docs",
                "api_prefix": settings.api_prefix,
            }

        logger.info("Frontend build not found, serving API only")

    return app


# Default app instance
app = create_app()
