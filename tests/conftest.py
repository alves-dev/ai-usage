"""Shared test fixtures for AI Usage."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))


@pytest.fixture
def codex_payload() -> dict[str, Any]:
    """Return a valid Codex payload."""
    return {
        "schema_version": "2.0",
        "collector_data": {
            "id": "manual_test",
            "version": "1.0.0",
            "transport": "test",
        },
        "collected_at": "2026-06-03T18:30:00.000Z",
        "provider": "codex",
        "status": "ok",
        "account_data": {
            "id": "acct-manual-codex",
            "id_kind": "provider_account_id",
            "label": "Codex manual",
            "email": "codex.manual@example.com",
            "plan": {"type": "plus"},
        },
        "usage_data": {
            "windows": [
                {
                    "id": "short",
                    "label": "5-hour window",
                    "duration_seconds": 18000,
                    "used_percent": 12.5,
                    "reset_after_seconds": 14400,
                    "reset_at": "2026-06-03T22:30:00.000Z",
                    "limit_reached": False,
                },
                {
                    "id": "long",
                    "label": "Weekly window",
                    "duration_seconds": 604800,
                    "used_percent": 37.2,
                    "reset_after_seconds": 428946,
                    "reset_at": "2026-06-08T00:00:00.000Z",
                    "limit_reached": False,
                },
            ]
        },
        "error": None,
    }


@pytest.fixture
def ollama_payload() -> dict[str, Any]:
    """Return a valid Ollama Cloud payload."""
    return {
        "schema_version": "2.0",
        "collector_data": {
            "id": "manual_test",
            "version": "1.0.0",
            "transport": "test",
        },
        "collected_at": "2026-06-03T18:30:00.000Z",
        "provider": "ollama_cloud",
        "status": "ok",
        "account_data": {
            "id": "ollama-account-manual",
            "id_kind": "provider_account_id",
            "label": "Ollama manual",
            "username": "ollama-manual",
            "email": "ollama.manual@example.com",
            "plan": {"type": "free"},
        },
        "usage_data": {
            "windows": [
                {
                    "id": "session",
                    "label": "Session window",
                    "duration_seconds": 18000,
                    "used_percent": 8.0,
                    "reset_at": "2026-06-03T22:00:00.000Z",
                    "limit_reached": False,
                },
                {
                    "id": "weekly",
                    "label": "Weekly window",
                    "duration_seconds": 604800,
                    "used_percent": 44.4,
                    "reset_at": "2026-06-08T00:00:00.000Z",
                    "limit_reached": False,
                },
            ]
        },
        "error": None,
    }


@pytest.fixture
def error_payload() -> dict[str, Any]:
    """Return a valid provider error payload without account identity."""
    return {
        "schema_version": "2.0",
        "collector_data": {
            "id": "manual_test",
            "version": "1.0.0",
            "transport": "test",
        },
        "collected_at": "2026-06-03T18:30:00.000Z",
        "provider": "codex",
        "status": "not_authenticated",
        "account_data": {},
        "usage_data": {"windows": []},
        "error": {
            "code": "not_authenticated",
            "message": "Manual test: user is not logged in",
        },
    }


def clone_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a deep copy of a payload fixture."""
    return deepcopy(payload)
