.PHONY: install compile generate mock dev build typecheck clean api all \
        backend-install backend-dev backend backend-migrate backend-migration backend-test backend-lint

# Install root + frontend + backend deps
install:
	npm install
	cd frontend && npm install
	$(MAKE) backend-install

# Regenerate OpenAPI + Python client from TypeSpec
compile:
	npx tsp compile .

# Regenerate orval hooks from the OpenAPI spec (requires `make compile`)
generate:
	cd frontend && npm run generate:api

# Full contract pipeline: compile → generate → typecheck
api: compile generate typecheck

# Prism mock server on :4010 (requires `make compile`)
mock:
	cd frontend && npm run mock

# Vite dev server on :5173 (run `make mock` in another terminal first)
dev:
	cd frontend && npm run dev

# Production build
build:
	cd frontend && npm run build

# TypeScript check (no emit)
typecheck:
	cd frontend && npm run typecheck

# ---- Backend (backend/) ----

# Install backend deps via uv
backend-install:
	cd backend && uv sync

# Run uvicorn dev server on :8000 with reload
backend-dev:
	cd backend && uv run uvicorn app.main:app --reload --port 8000

# Alias for the dev server
backend: backend-dev

# Apply Alembic migrations to head
backend-migrate:
	cd backend && uv run alembic upgrade head

# Create a new autogenerate migration: make backend-migration MSG="create users"
backend-migration:
	cd backend && uv run alembic revision --autogenerate -m "$(MSG)"

# Run the backend test suite
backend-test:
	cd backend && uv run pytest

# Lint + format check
backend-lint:
	cd backend && uv run ruff check . && uv run ruff format --check .

# Remove build artifacts
clean:
	rm -rf tsp-output frontend/dist frontend/src/api/generated \
		backend/.venv backend/data/*.db backend/data/*.db-journal backend/data/*.sqlite* \
		backend/.pytest_cache backend/.ruff_cache

# Everything: install → contract → migrate → build
all: install api backend-migrate build
