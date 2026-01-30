"""
Main entry point for Wiki-Craft.

Provides both CLI and programmatic access to the application.
"""

import logging
import sys

import uvicorn

from wiki_craft.config import settings


def setup_logging() -> None:
    """Configure logging for the application."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Reduce noise from libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)


def run_server(
    host: str | None = None,
    port: int | None = None,
    reload: bool = False,
) -> None:
    """
    Run the FastAPI server.

    Args:
        host: Host to bind to
        port: Port to listen on
        reload: Enable auto-reload for development
    """
    setup_logging()

    uvicorn.run(
        "wiki_craft.api.app:app",
        host=host or settings.host,
        port=port or settings.port,
        reload=reload,
        log_level=settings.log_level.lower(),
    )


def cli() -> None:
    """Command-line interface entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Wiki-Craft: Document ingestion and wiki generation system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  wiki-craft serve                    Start the API server
  wiki-craft serve --port 8080        Start on custom port
  wiki-craft serve --reload           Start with auto-reload
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start the API server")
    serve_parser.add_argument("--host", default=None, help="Host to bind to")
    serve_parser.add_argument("--port", type=int, default=None, help="Port to listen on")
    serve_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest a document")
    ingest_parser.add_argument("file", help="File to ingest")
    ingest_parser.add_argument("--metadata", help="JSON metadata string")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search the knowledge base")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--limit", type=int, default=5, help="Max results")

    # Wiki command
    wiki_parser = subparsers.add_parser("wiki", help="Generate wiki entry")
    wiki_parser.add_argument("topic", help="Topic or question")
    wiki_parser.add_argument("--format", choices=["markdown", "html", "json"], default="markdown")
    wiki_parser.add_argument("--output", "-o", help="Output file")

    # Stats command
    subparsers.add_parser("stats", help="Show knowledge base statistics")

    args = parser.parse_args()

    if args.command == "serve":
        run_server(host=args.host, port=args.port, reload=args.reload)

    elif args.command == "ingest":
        from pathlib import Path
        from wiki_craft.parsers import ParserRegistry
        from wiki_craft.processing.chunker import chunk_document
        from wiki_craft.storage.vector_store import get_vector_store

        setup_logging()
        file_path = Path(args.file)

        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            sys.exit(1)

        parser = ParserRegistry.get_parser(file_path)
        if not parser:
            print(f"Error: Unsupported file type: {file_path.suffix}")
            sys.exit(1)

        print(f"Parsing {file_path}...")
        document = parser.parse(file_path)

        print(f"Chunking document...")
        chunks = chunk_document(document)

        print(f"Storing {len(chunks)} chunks...")
        store = get_vector_store()
        store.add_chunks(chunks)

        print(f"Done! Document ID: {document.metadata.document_id}")

    elif args.command == "search":
        from wiki_craft.storage.vector_store import get_vector_store
        from wiki_craft.storage.models import SearchQuery

        setup_logging()
        store = get_vector_store()

        query = SearchQuery(query=args.query, limit=args.limit)
        response = store.search(query)

        print(f"\nFound {response.total_results} results for '{args.query}':\n")
        for i, result in enumerate(response.results, 1):
            print(f"{i}. [{result.score:.3f}] {result.metadata.document_title or result.metadata.source_path}")
            print(f"   {result.text[:200]}...")
            print()

    elif args.command == "wiki":
        from wiki_craft.storage.vector_store import get_vector_store
        from wiki_craft.wiki.generator import WikiGenerator
        from wiki_craft.wiki.formatter import WikiFormatter

        setup_logging()
        store = get_vector_store()

        print(f"Generating wiki entry for: {args.topic}\n")
        generator = WikiGenerator(store)
        entry = generator.generate(args.topic)

        content = WikiFormatter.format(entry, args.format)

        if args.output:
            with open(args.output, "w") as f:
                f.write(content)
            print(f"Written to {args.output}")
        else:
            print(content)

    elif args.command == "stats":
        from wiki_craft.storage.vector_store import get_vector_store

        setup_logging()
        store = get_vector_store()
        documents = store.list_documents()

        print("\n=== Wiki-Craft Knowledge Base Stats ===\n")
        print(f"Total Documents: {len(documents)}")
        print(f"Total Chunks: {store.count}")

        if documents:
            print(f"\nDocuments:")
            for doc in documents[:10]:
                print(f"  - {doc.get('document_title') or doc.get('source_path')} ({doc.get('total_chunks', 0)} chunks)")
            if len(documents) > 10:
                print(f"  ... and {len(documents) - 10} more")

    else:
        parser.print_help()


if __name__ == "__main__":
    cli()
