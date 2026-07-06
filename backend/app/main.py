"""FastAPI application factory.

Mounts every feature router under the prefixes declared in `main.tsp` and wires
the shared error handlers. Endpoints return 501 stubs for now.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.core.errors import register_error_handlers
from app.features.bookings.router import router as bookings_router
from app.features.event_types.router import router as event_types_router
from app.features.public.router import router as public_router
from app.features.schedules.router import router as schedules_router
from app.features.users.router import router as users_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Cal Killer",
        version="0.1.0",
        description="Backend for Cal Killer — FastAPI implementation of the TypeSpec contract.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_error_handlers(app)

    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(schedules_router)
    app.include_router(event_types_router)
    app.include_router(bookings_router)
    app.include_router(public_router)

    @app.get("/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    # Раздаём собранную Vite-статику из Docker-образа (единый origin на :8000).
    # Локальный dev (без /app/static) этот mount пропускает — Vite сам отдаёт статику.
    static_dir = Path("/app/static")
    if static_dir.is_dir():
        from fastapi.staticfiles import StaticFiles

        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="spa")

    return app


app = create_app()
