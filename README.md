# cal-killer

TypeSpec-контракт + React/Vite фронтенд + FastAPI бэкенд на SQLAlchemy 2 + SQLite.

## Требования

- Node 18+, npm 11.18.0 (зафиксирован в корневом `package.json`)
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

## Подробнее

- [`AGENTS.md`](./AGENTS.md) — архитектура, конвенции кода, gotchas.
- [`CONTEXT.md`](./CONTEXT.md) — продуктовый контекст проекта.
