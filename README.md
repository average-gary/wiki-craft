# Wiki-Craft

Document ingestion and indexing system for building wiki-style knowledge bases with full source tracking.

## Features

- **Multi-format Document Parsing**: PDF (with OCR), Word, Excel, Markdown, HTML, EPUB
- **Semantic Search**: Vector embeddings with ChromaDB for intelligent retrieval
- **Wiki Generation**: Auto-generate wiki articles from your document corpus
- **Source Attribution**: Full traceability back to original documents
- **Web Interface**: React frontend with dark mode support

## Quick Start

Requires [just](https://github.com/casey/just) command runner.

```bash
# One command to install everything and start the server
just run
```

Then visit http://localhost:8000

## Manual Setup

### Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
wiki-craft serve
```

### Frontend (for development)

```bash
cd frontend
npm install
npm run dev
```

## Available Commands

Run `just` to see all available commands:

| Command | Description |
|---------|-------------|
| `just run` | Install deps, build frontend, start server |
| `just install` | Install all dependencies |
| `just serve` | Start the backend server |
| `just dev-backend` | Backend with hot reload |
| `just dev-frontend` | Frontend dev server with HMR |
| `just clean` | Remove build artifacts |
| `just fresh` | Clean + reinstall everything |

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Architecture

```
wiki-craft/
├── src/wiki_craft/
│   ├── api/           # FastAPI routes
│   ├── parsers/       # Document parsers (PDF, DOCX, etc.)
│   ├── processing/    # Chunking and text processing
│   ├── storage/       # ChromaDB vector store
│   ├── embeddings/    # Sentence transformers
│   └── wiki/          # Wiki generation
└── frontend/          # React + TypeScript + shadcn/ui
```

## License

MIT
