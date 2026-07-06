# AGENTS.md

Three-part repo: a TypeSpec API contract at the root, a React/Vite frontend in `frontend/`, and a FastAPI backend in `backend/`. The frontend runs against either a Prism mock (`:4010`) or the real backend (`:8000`) of the generated OpenAPI spec. Domain language lives in `CONTEXT.md` (User/Owner/EventType/Schedule/Booking vocabulary) — reuse it instead of inventing synonyms.

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

### Required order when changing the API contract
`main.tsp` → `npx tsp compile .` → `cd frontend && npm run generate:api` → `npm run typecheck`. Skipping the orval step leaves `src/api/generated/` stale and TypeScript will fail on the changed types.

Shortcut: `make api` runs compile → generate → typecheck; `make all` runs install → api → backend-migrate → build; `make clean` wipes build artifacts (tsp-output, generated api, venv, db files). `make dev`/`make mock`/`make build` delegate to the frontend scripts. Use the Makefile rather than re-typing the chain.

## Architecture notes

- `frontend/src/api/client-config.ts` is the orval mutator (`customFetch`). It injects Bearer tokens from `@/auth/token-storage`, auto-refreshes on 401 (dedupes concurrent refreshes), and unwraps `{ data, status, headers }`. Don't bypass it — orval-generated hooks call `customFetch` by name.
- Vite path alias: `@/*` → `frontend/src/*` (configured in both `vite.config.ts` and `tsconfig.json`).
- orval runs in `tags-split` + `react-query` + `fetch` mode. Generated hooks live under `src/api/generated/<tag>/`. Generated files are auto-formatted with prettier on write (`afterAllFilesWrite` in `orval.config.ts`) — don't hand-edit or reformat them.
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

## CI

GitHub Actions in `.github/workflows/ci.yml`. Triggers on push to `main` and on pull requests. Concurrency group cancels superseded PR runs.

Jobs:
- `gitleaks` — unconditional and blocking; mirrors the local pre-commit hook.
- `frontend` — `tsp compile` → `generate:api` (orval) → `typecheck` → `build`; uploads `frontend/dist` as an artifact.
- `backend-lint` — `ruff check . && ruff format --check .` via `uv run`.
- `backend-test` — `tsp compile` (needed for `tests/api/test_contract_match.py`) → `uv sync --frozen` → `uv run pytest`.

`frontend`, `backend-lint`, and `backend-test` are gated by `dorny/paths-filter` and skip when only unrelated paths (docs, README) change. `backend-test` also runs on contract-touching files (`main.tsp`, orval/client-config).

Pinned versions: Node `24.18.0`, npm `11.18.0` (matches root `packageManager`), Python `3.12` (via `backend/.python-version`), uv via `astral-sh/setup-uv@v6`. `backend/uv.lock` is committed and CI uses `uv sync --frozen` — keep the lockfile updated when changing `backend/pyproject.toml`.

## Deploy (Docker)

Single multi-stage image built from the root `Dockerfile`: Vite static is produced in stage 1, FastAPI serves it on `/` in stage 3, so frontend and backend share one origin on `:8000`.

- Published to GHCR **only** on git tags matching `v*.*.*` (job `docker`). Tags `1.2.3`, `1.2`, `1`, and `latest` are derived via `docker/metadata-action`. No deploys happen from branch pushes.
- Container runs `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000` — migrations auto-apply on every boot against the SQLite in `/app/data`.
- `VOLUME /app/data` persists SQLite across container recreation; mount a named volume to keep it.
- Healthcheck: `GET http://localhost:8000/health` → `{"status":"ok"}`.
- Image is built with `--no-dev`, so dev-only tools (`pytest`, `ruff`, `httpx`, `pyyaml`) are absent at runtime — don't write runtime code that imports them.
- Runtime config is env-driven; see `backend/app/config.py`. Defaults: `DATABASE_URL=sqlite:///./data/calkiller.db`, `JWT_SECRET=change-me-in-production` (must override in prod), `JWT_ALG=HS256`, `JWT_ACCESS_TTL_MINUTES=15`, `JWT_REFRESH_TTL_DAYS=30`.
- The `@typespec/http-client-python` emitter is intentionally skipped during the image build (it needs Pyodide + CDN access, unreliable in isolated networks). The Python client is gitignored and unused by both apps — don't add it back to the build.
