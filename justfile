# Wiki-Craft Justfile
# Run `just` to see available commands

# Use python3/pip3 explicitly for macOS compatibility
python := "python3"
pip := "pip3"

# Default recipe - show help
default:
    @just --list

# Install all dependencies (Python + Node)
install:
    {{pip}} install -e .
    cd frontend && npm install

# Install Python backend only
install-backend:
    {{pip}} install -e .

# Install frontend dependencies only
install-frontend:
    cd frontend && npm install

# Build frontend for production
build-frontend:
    cd frontend && npm run build

# Run the full stack (install, build, serve)
run: install build-frontend serve

# Start the backend server (serves frontend if built)
serve:
    wiki-craft serve

# Start backend with auto-reload for development
dev-backend:
    uvicorn wiki_craft.api.app:app --reload --host 0.0.0.0 --port 8000

# Start frontend dev server with hot reload
dev-frontend:
    cd frontend && npm run dev

# Run both frontend and backend in dev mode (requires two terminals)
dev:
    @echo "Starting development servers..."
    @echo "Run 'just dev-backend' in one terminal"
    @echo "Run 'just dev-frontend' in another terminal"
    @echo "Frontend: http://localhost:5173"
    @echo "Backend:  http://localhost:8000"

# Clean build artifacts
clean:
    rm -rf frontend/dist
    rm -rf frontend/node_modules
    rm -rf build/
    rm -rf *.egg-info
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true

# Clean and reinstall everything
fresh: clean install build-frontend

# Run Python tests
test:
    {{python}} -m pytest

# Run frontend linting
lint-frontend:
    cd frontend && npm run lint

# Type check frontend
typecheck-frontend:
    cd frontend && npx tsc --noEmit

# Check health of running server
health:
    curl -s http://localhost:8000/health | python3 -m json.tool

# Show API documentation URL
docs:
    @echo "API Docs: http://localhost:8000/docs"
    @echo "ReDoc:    http://localhost:8000/redoc"
