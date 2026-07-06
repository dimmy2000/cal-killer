# syntax=docker/dockerfile:1.7

# ============================================================================
# Stage 1: frontend-builder
# Компилирует TypeSpec → OpenAPI, генерирует orval hooks, собирает Vite-статику.
# ============================================================================
FROM node:24.18.0-bookworm-slim AS frontend-builder

# Пиннинг npm (как в корневом package.json -> packageManager)
RUN npm install -g npm@11.18.0

WORKDIR /repo

# Сначала копируем lock-файлы и манифесты для кеширования слоёв установки.
COPY package.json package-lock.json ./
COPY frontend/package.json frontend/package-lock.json frontend/
COPY tspconfig.yaml main.tsp ./

# Установка зависимостей root (TypeSpec) и frontend.
RUN --mount=type=cache,target=/root/.npm \
    npm ci \
    && cd frontend && npm ci

# Теперь исходники (всё, что не в .dockerignore).
COPY frontend/ ./frontend/

# 1) TypeSpec → OpenAPI (пишет в tsp-output/schema/openapi.yaml, нужен orval'у и runtime).
#    Эмиттер @typespec/http-client-python намеренно пропущен: он гоняется под
#    Pyodide (WASM Python) и тянет пакеты из CDN, что в изолированной Docker-сети
#    ненадёжно. Python-клиент всё равно gitignored и не нужен ни frontend, ни backend.
# 2) orval → frontend/src/api/generated/
# 3) typecheck
# 4) vite build → frontend/dist/
RUN npx tsp compile . --emit @typespec/openapi3 \
    && cd frontend \
    && npm run generate:api \
    && npm run typecheck \
    && npm run build

# ============================================================================
# Stage 2: backend-builder
# Ставит production-зависимости через uv (без dev-group).
# ============================================================================
FROM python:3.12-slim AS backend-builder

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv

# Ставим uv (pin версии через копию lock-файла для воспроизводимости).
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Копируем только манифест зависимостей — кеш слоёв.
COPY backend/pyproject.toml backend/uv.lock ./

# Синхронизация без dev-зависимостей (pytest/ruff/httpx/pyyaml не нужны в prod).
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Копируем исходники backend'а.
COPY backend/app ./app
COPY backend/alembic ./alembic
COPY backend/alembic.ini ./

# Копируем сгенерированный OpenAPI — нужен для runtime (contract endpoint и т.п.).
COPY --from=frontend-builder /repo/tsp-output ./tsp-output

# ============================================================================
# Stage 3: runtime
# Минимальный образ: venv + app + alembic + static + OpenAPI.
# ============================================================================
FROM python:3.12-slim AS runtime

# Минимальные runtime-зависимости: curl для healthcheck, tzdata для корректного времени.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    DATABASE_URL=sqlite:///./data/calkiller.db

WORKDIR /app

# Virtualenv с прод-зависимостями.
COPY --from=backend-builder /app/.venv /app/.venv

# Код backend + миграции.
COPY --from=backend-builder /app/app /app/app
COPY --from=backend-builder /app/alembic /app/alembic
COPY --from=backend-builder /app/alembic.ini /app/alembic.ini

# Сгенерированный OpenAPI (если нужен в runtime).
COPY --from=backend-builder /app/tsp-output /app/tsp-output

# Frontend-статика, которую FastAPI будет раздавать на /.
COPY --from=frontend-builder /repo/frontend/dist /app/static

# Volume для SQLite — данные переживают пересоздание контейнера.
RUN mkdir -p /app/data
VOLUME /app/data

EXPOSE 8000

# Миграции + запуск uvicorn.
# alembic upgrade head применяет неприменённые миграции к SQLite в /app/data.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
