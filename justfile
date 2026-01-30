# Wiki-Craft Justfile
# Run `just` to see available commands

# Virtual environment directory
venv_dir := ".venv"
python := venv_dir / "bin/python"
pip := venv_dir / "bin/pip"

# Default recipe - show help
default:
    @just --list

# Create virtual environment if it doesn't exist
venv:
    #!/usr/bin/env bash
    if [ ! -d "{{venv_dir}}" ]; then
        echo "Creating virtual environment..."
        python3 -m venv {{venv_dir}}
    fi

# Install all dependencies (Python + Node)
install: venv
    {{pip}} install -e .
    cd frontend && npm install

# Install Python backend only
install-backend: venv
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
serve: venv
    {{python}} -m wiki_craft.main serve

# Start backend with auto-reload for development
dev-backend: venv
    {{venv_dir}}/bin/uvicorn wiki_craft.api.app:app --reload --host 0.0.0.0 --port 8000

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

# Clean everything including venv
clean-all: clean
    rm -rf {{venv_dir}}

# Clean and reinstall everything
fresh: clean-all install build-frontend

# Run Python tests
test: venv
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

# Activate venv instructions
activate:
    @echo "Run: source {{venv_dir}}/bin/activate"
