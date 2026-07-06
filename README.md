# cal-killer

Self-hosted инструмент для бронирования встреч. Владелец (User) публикует
шаблоны встреч (EventType) по адресу `/{ownerSlug}/{eventSlug}`; гости бронируют
слот без регистрации и управляют своим бронированием (Booking) по ссылке с
ManageToken. Доступность считается из расписания владельца (Schedule = рабочие
часы + переопределения) минус уже занятые слоты — подробно см.
[`CONTEXT.md`](./CONTEXT.md).

Стек: TypeSpec-контракт + React/Vite (Mantine + react-query) + FastAPI на
SQLAlchemy 2 + Alembic + SQLite.

## Структура репо

| Путь                | Что внутри                                              |
| ------------------- | ------------------------------------------------------- |
| `main.tsp`          | TypeSpec API-контракт — единый источник правды для API  |
| `frontend/`         | React/Vite + Mantine, orval-генерация хуков из OpenAPI  |
| `backend/`          | FastAPI + SQLAlchemy 2 + Alembic + SQLite, домены по тегам |
| `docs/adr/`         | Архитектурные решения (lifecycle, timezone, автоотмена stale и др.) |
| `CONTEXT.md`        | Доменный язык проекта (ubiquitous language)             |
| `AGENTS.md`         | Архитектура, конвенции кода, gotchas                    |

## Требования

- Node 24.18.0, npm 11.18.0 (зафиксированы в корневом `package.json` и CI)
- Python 3.12 + [`uv`](https://docs.astral.sh/uv/)
- Один раз установить зависимости всего репо:

  ```bash
  make install
  ```

## Порты

| Сервис     | Порт | Когда используется          |
| ---------- | ---- | ---------------------------- |
| Vite       | 5173 | всегда (фронтенд)            |
| FastAPI    | 8000 | режим «фронтенд + бэкенд+БД» |
| Prism mock | 4010 | режим «отладка с моками»     |

## Режим 1 — отладка фронтенда с моками (без бэкенда)

```bash
# 1. Сгенерировать OpenAPI из TypeSpec (нужен для запуска мока)
make compile

# 2. Терминал A — Prism mock на :4010
make mock

# 3. Терминал B — Vite на :5173 (по умолчанию прокси → :4010)
make dev
```

Открыть http://localhost:5173

## Режим 2 — фронтенд + реальный бэкенд + SQLite

```bash
# 1. Установить зависимости бэкенда (если ещё не делалось)
make backend-install

# 2. Применить мигции (создаст backend/data/calkiller.db)
make backend-migrate

# 3. Терминал A — uvicorn на :8000 с автоперезагрузкой
make backend-dev

# 4. Терминал B — Vite на :5173 с прокси на бэкенд
VITE_API_TARGET=http://localhost:8000 make dev
```

Открыть http://localhost:5173

## Остановка

`Ctrl+C` в каждом терминале.

## Частые задачи

- Сменить схему БД: `make backend-migration MSG="create users"`
- Перегенерировать контракт (TypeSpec → OpenAPI → orval): `make api`
  (полный пайплайн compile → generate → typecheck)
- Полный прогон install → api → migrate → build: `make all`
- Тесты бэкенда: `make backend-test`
- Линт + формат бэкенда: `make backend-lint`
- Полный сброс артефактов (tsp-output, сгенерированный API, venv, БД): `make clean`

## Замечания

- По умолчанию `make dev` ходит на Prism mock `:4010`. Чтобы ходить на реальный
  бэкенд, **всегда** передавай `VITE_API_TARGET=http://localhost:8000`.
- Чтобы не печатать это каждый раз, создай `frontend/.env.local` со строкой:

  ```
  VITE_API_TARGET=http://localhost:8000
  ```

  Vite подхватит его автоматически. Файл попадает под `.gitignore` (паттерн `.env*`).
- БД — SQLite в `backend/data/calkiller.db`. Тестовая — `backend/data/calkiller.test.db`.
  `make clean` удалит обе.
- `tsp-output/` и `frontend/src/api/generated/` — билд-артефакты; не редактируй их вручную,
  перегенерируй через `make api`.
- `frontend/tsconfig.json` включает `noUnusedLocals` и `noUnusedParameters` —
  чисти неиспользуемые переменные и импорты перед `make typecheck`, иначе сборка упадёт.

## Деплой через Docker

Сервис упакован в один Docker-образ (`Dockerfile` в корне репо): внутри
собирается Vite-статика и FastAPI её раздаёт на `/`, поэтому фронтенд и бэкенд
работают на одном origin `:8000`. Образ публикуется в GitHub Container Registry
только при пуше git-тега `v*.*.*` (см. job `docker` в CI).

### Переменные окружения

| Переменная                  | По умолчанию                       | Что задаёт                          |
| --------------------------- | ---------------------------------- | ----------------------------------- |
| `DATABASE_URL`              | `sqlite:///./data/calkiller.db`    | URL БД (SQLite по умолчанию)        |
| `JWT_SECRET`                | `change-me-in-production`          | Секрет для подписи JWT (поменяй!)   |
| `JWT_ALG`                   | `HS256`                            | Алгоритм JWT                        |
| `JWT_ACCESS_TTL_MINUTES`    | `15`                               | TTL access-токена (минуты)          |
| `JWT_REFRESH_TTL_DAYS`      | `30`                               | TTL refresh-токена (дни)            |
| `PORT`                      | `8000`                             | Порт (фикс в `CMD`, оставь 8000)    |

### Запуск опубликованного образа

```bash
docker pull ghcr.io/<owner>/<repo>:latest

docker run -d \
  --name calkiller \
  -p 8000:8000 \
  -e JWT_SECRET="$(openssl rand -hex 32)" \
  -v calkiller-data:/app/data \
  --restart unless-stopped \
  ghcr.io/<owner>/<repo>:latest
```

- Volume `calkiller-data` сохраняет SQLite между рестартами контейнера
  (`VOLUME /app/data` объявлен в образе).
- При старте контейнера автоматически выполняется `alembic upgrade head` —
  миграции применяются к свежей или существующей БД.
- Healthcheck: `GET http://localhost:8000/health` → `{"status": "ok"}`.

### Локальная сборка образа (для отладки)

```bash
docker build -t calkiller:local .
docker run --rm -p 8000:8000 -e JWT_SECRET=dev-secret -v calkiller-data:/app/data calkiller:local
```

### Релиз нового образа

```bash
git tag v1.2.3
git push origin v1.2.3
```

CI соберёт образ и опубликует теги `1.2.3`, `1.2`, `1` и `latest` в
`ghcr.io/<owner>/<repo>`.

## Подробнее

- [`CONTEXT.md`](./CONTEXT.md) — доменный язык проекта (User / EventType / Schedule /
  Booking / Attendee и др.): что значат термины и каких синонимов избегать.
- [`docs/adr/`](./docs/adr/) — архитектурные решения:
  reschedule-in-place (0001), сохранение wall-clock при смене timezone (0002),
  свободные переходы lifecycle с `cancelled` терминальным (0003),
  доступность слотов scoped to Schedule (0004), автоотмена stale pending/rescheduled (0005),
  refresh-token rotation без grace window (0006).
- [`AGENTS.md`](./AGENTS.md) — архитектура, конвенции кода, gotchas.
