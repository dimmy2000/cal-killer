# Cal Killer backend

Python 3.12 + FastAPI + SQLAlchemy 2 (sync) + Alembic + SQLite, managed with `uv`.

## Setup

```bash
make backend-install      # uv sync
make backend-migrate      # alembic upgrade head
make backend-dev          # uvicorn on :8000 (reload)
```

Or run directly from `backend/`:

```bash
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

## Ports

- Backend: `:8000`
- Prism mock (still available): `:4010`
- Frontend dev: `:5173` — point at backend with `VITE_API_TARGET=http://localhost:8000 npm run dev`

## Commands

| Command              | Action                                          |
| -------------------- | ----------------------------------------------- |
| `make backend-install`  | `uv sync`                                    |
| `make backend-dev`      | uvicorn reload on :8000                      |
| `make backend-migrate`  | `alembic upgrade head`                       |
| `make backend-migration MSG="..."` | `alembic revision --autogenerate`  |
| `make backend-test`     | `uv run pytest`                              |
| `make backend-lint`     | `ruff check` + `ruff format --check`         |

## Contract

Routes are written by hand against `main.tsp`. `tests/api/test_contract_match.py`
compares the FastAPI app's OpenAPI paths against `../tsp-output/schema/openapi.yaml`
to catch drift — run `make compile` first so the spec exists.

Endpoints currently return `501 Not Implemented` stubs.
