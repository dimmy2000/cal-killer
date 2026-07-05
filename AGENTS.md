# AGENTS.md

Two-package repo: a TypeSpec API contract at the root, a React/Vite frontend in `frontend/`, and a FastAPI backend in `backend/`. The frontend runs against either a Prism mock (`:4010`) or the real backend (`:8000`) of the generated OpenAPI spec.

## Commands

### Root (TypeSpec)
- `npx tsp compile .` — regenerate `tsp-output/`. Emits OpenAPI to `tsp-output/schema/openapi.yaml` and a Python client to `tsp-output/clients/python/` (both gitignored).
- `tsp-output/` is the build artifact; never edit it by hand. Edit `main.tsp` and recompile.
- Root `package.json` has no `scripts` block — invoke `tsp` directly.

### Frontend (`frontend/`)
- `npm run dev` — Vite dev server on :5173. Proxies `/api` → `http://localhost:4010` (strips `/api`), so run the mock first.
- `npm run mock` — Prism mock server on :4010 from `../tsp-output/schema/openapi.yaml`. Requires `tsp compile` to have run.
- `npm run generate:api` — orval codegen. Reads `../tsp-output/schema/openapi.yaml`, writes `src/api/generated/` (gitignored). Requires `tsp compile` first.
- `npm run typecheck` — `tsc --noEmit`.
- `npm run build` — `tsc -b && vite build`.
- No test suite exists.

### Backend (`backend/`)
Python 3.12 + FastAPI + SQLAlchemy 2 (sync) + Alembic + SQLite, managed with `uv`. Endpoints are stubbed to `501` until implemented; routes are written by hand against `main.tsp`.
- `make backend-install` — `uv sync`.
- `make backend-migrate` — `alembic upgrade head`.
- `make backend-dev` (alias `make backend`) — uvicorn on :8000 with reload.
- `make backend-migration MSG="..."` — `alembic revision --autogenerate`.
- `make backend-test` — `uv run pytest`.
- `make backend-lint` — `ruff check . && ruff format --check .`.
- Start order: `make backend-install` → `make backend-migrate` → `make backend-dev`.

Ports: backend on `:8000`, Prism mock stays on `:4010`. Point the frontend at the backend with `VITE_API_TARGET=http://localhost:8000 npm run dev` (default stays on the mock at `:4010`).

`tests/api/test_contract_match.py` diffs the FastAPI app's OpenAPI against `tsp-output/schema/openapi.yaml` — run `make compile` first so the spec exists.

### Required order when changing the API contract
`main.tsp` → `npx tsp compile .` → `cd frontend && npm run generate:api` → `npm run typecheck`. Skipping the orval step leaves `src/api/generated/` stale and TypeScript will fail on the changed types.

Shortcut: `make api` runs compile → generate → typecheck; `make all` runs install → api → backend-migrate → build; `make clean` wipes build artifacts (tsp-output, generated api, venv, db files). `make dev`/`make mock`/`make build` delegate to the frontend scripts. Use the Makefile rather than re-typing the chain.

## Architecture notes

- `frontend/src/api/client-config.ts` is the orval mutator (`customFetch`). It injects Bearer tokens from `@/auth/token-storage`, auto-refreshes on 401 (dedupes concurrent refreshes), and unwraps `{ data, status, headers }`. Don't bypass it — orval-generated hooks call `customFetch` by name.
- Vite path alias: `@/*` → `frontend/src/*` (configured in both `vite.config.ts` and `tsconfig.json`).
- orval runs in `tags-split` + `react-query` + `fetch` mode. Generated hooks live under `src/api/generated/<tag>/`.
- Feature modules live under `frontend/src/features/<domain>/` (auth, bookings, event-types, schedules, profile, public-booking, guest-manage). UI primitives are in `src/components/`.
- Backend mirrors the API tags: route handlers live in `backend/app/features/<domain>/` (bookings, event_types, public, schedules, users), with `app/auth/` for JWT/Depends wiring. Tests mirror this layout under `backend/tests/{api,unit}/` — `tests/api/test_<tag>.py` per tag plus `test_contract_match.py`.
- The contract test (`tests/api/test_contract_match.py`) diffs the FastAPI app's OpenAPI against `tsp-output/schema/openapi.yaml` — run `make compile` first so the spec exists. Test DB is isolated to `backend/data/calkiller.test.db` via `conftest.py`.

## Conventions / gotchas

- `tsconfig.json` enables `noUnusedLocals` and `noUnusedParameters` — clean up unused vars/imports before typechecking or the build will fail.
- `packageManager` is pinned to npm 11.18.0 in root `package.json`; do not switch to pnpm/yarn.
- Pre-commit only runs gitleaks (`.pre-commit-config.yaml`). Install with `pre-commit install`.
- `.gitignore` blocks many secret file patterns (`.env*`, `*.pem`, `*.key`, `credentials.*`, etc.) — don't try to commit fixtures with those names.
- Mantine 7 + PostCSS requires `postcss-preset-mantine` and `postcss-simple-vars` (already wired in `frontend/postcss.config.cjs`); Mantine CSS imports must go through PostCSS, not Tailwind.
- Backend ruff ignores `E501`, `B008` (so FastAPI's `Depends()`/`Query()` in argument defaults is idiomatic — don't "fix" it), and `UP046`. Line length 100; rule set `E,F,I,UP,B,SIM,RUF`.
