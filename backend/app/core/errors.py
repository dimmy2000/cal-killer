"""Error envelope and exception handlers matching the `Error` model in main.tsp."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorBody(BaseModel):
    code: int
    message: str
    details: str | None = None


class BackendError(Exception):
    """Raise from a route/service to return a structured Error response."""

    def __init__(self, code: int, message: str, details: str | None = None) -> None:
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(BackendError)
    async def _backend_error_handler(_request: Request, exc: BackendError) -> JSONResponse:
        body = ErrorBody(code=exc.code, message=exc.message, details=exc.details)
        return JSONResponse(status_code=exc.code, content=body.model_dump(exclude_none=True))
