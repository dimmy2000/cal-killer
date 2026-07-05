"""Shared pytest fixtures.

The TestClient uses the real app with its real SQLite engine. Tests that hit
endpoints rely on the 501 stubs for now; once persistence lands, swap in an
in-memory SQLite engine here.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure the backend package is importable when running from the repo root.
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Use a throwaway SQLite file for the test process so we never touch the dev db.
os.environ.setdefault("DATABASE_URL", "sqlite:///./data/calkiller.test.db")

from app.main import app  # noqa: E402


@pytest.fixture()
def client() -> TestClient:
    with TestClient(app) as c:
        yield c
