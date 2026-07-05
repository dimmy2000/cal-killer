"""Pagination helpers shared across list endpoints.

`PageQuery` is a pydantic model used as a dependency to parse `limit`/`cursor`
query params (matching `PageQuery` in `main.tsp`). `Paginated` is the generic
response envelope.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")

DEFAULT_LIMIT = 50
MAX_LIMIT = 200


class PageQuery(BaseModel):
    limit: int | None = None
    cursor: str | None = None


def page_query(
    limit: int | None = Query(default=None, ge=1, le=MAX_LIMIT),
    cursor: str | None = Query(default=None),
) -> PageQuery:
    return PageQuery(limit=limit, cursor=cursor)


class Paginated(BaseModel, Generic[T]):
    items: list[T]
    nextCursor: str | None = None
