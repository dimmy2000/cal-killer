"""Contract drift test.

Loads `../tsp-output/schema/openapi.yaml` (produced by `make compile`) and
compares its path+method set against the FastAPI app's generated OpenAPI.

Every (method, path) in the TypeSpec contract must exist in the backend, and
every backend route must exist in the contract (except `/health`).

Run `make compile` first so the spec file exists.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

CONTRACT_PATH = Path(__file__).resolve().parents[3] / "tsp-output" / "schema" / "openapi.yaml"

# Routes the backend is allowed to add beyond the contract.
EXTRA_ALLOWED: set[tuple[str, str]] = {("get", "/health")}

HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


def _contract_paths() -> set[tuple[str, str]]:
    if not CONTRACT_PATH.exists():
        pytest.skip(f"contract spec not found at {CONTRACT_PATH} — run `make compile`")
    with CONTRACT_PATH.open() as f:
        spec = yaml.safe_load(f)
    out: set[tuple[str, str]] = set()
    for path, methods in (spec.get("paths") or {}).items():
        for method in methods:
            if method.lower() in HTTP_METHODS:
                out.add((method.lower(), path))
    return out


def _app_paths(client: TestClient) -> set[tuple[str, str]]:
    spec = client.get("/openapi.json").json()
    out: set[tuple[str, str]] = set()
    for path, methods in (spec.get("paths") or {}).items():
        for method in methods:
            if method.lower() in HTTP_METHODS:
                out.add((method.lower(), path))
    return out


def test_every_contract_route_exists_in_backend(client: TestClient) -> None:
    contract = _contract_paths()
    app_paths = _app_paths(client)
    missing = contract - app_paths
    assert not missing, f"backend is missing contract routes: {sorted(missing)}"


def test_backend_has_no_routes_outside_contract(client: TestClient) -> None:
    contract = _contract_paths()
    app_paths = _app_paths(client)
    extra = (app_paths - contract) - EXTRA_ALLOWED
    assert not extra, f"backend has routes not in contract: {sorted(extra)}"
