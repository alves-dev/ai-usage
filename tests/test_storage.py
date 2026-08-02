"""Tests for persisted AI Usage account metadata."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

from custom_components.ai_usage.models import AccountState
from custom_components.ai_usage.storage import (
    AIUsageStorage,
    _account_from_storage_item,
    _int_or_zero,
    _string_or_none,
)

EXPECTED_REQUEST_COUNT = 4
EXPECTED_THREE = 3


def test_storage_item_requires_supported_provider_and_key() -> None:
    """Malformed storage records should be ignored."""
    assert _account_from_storage_item(None) is None
    assert (
        _account_from_storage_item({"provider": "unknown", "account_key": "x"}) is None
    )
    assert _account_from_storage_item({"provider": "codex"}) is None


def test_storage_item_normalizes_fields_and_dates() -> None:
    """Valid records should restore account metadata safely."""
    state = _account_from_storage_item(
        {
            "provider": "codex",
            "account_key": " acct-test ",
            "account_key_quality": "",
            "account_label": " ",
            "account_data": {"email": "test@example.com"},
            "plan_data": {"type": "plus"},
            "request_count": "4",
            "last_seen_at": "2026-06-03T18:30:00+00:00",
        }
    )
    assert state is not None
    assert state.account_key == "acct-test"
    assert state.account_key_quality == "stable"
    assert state.account_label == "acct-test"
    assert state.request_count == EXPECTED_REQUEST_COUNT
    assert state.last_received_at == datetime(2026, 6, 3, 18, 30, tzinfo=UTC)

    invalid_date = _account_from_storage_item(
        {"provider": "codex", "account_key": "x", "last_seen_at": "bad"}
    )
    assert invalid_date is not None
    assert invalid_date.last_received_at is None


def test_storage_scalar_helpers() -> None:
    """Storage scalar conversion should reject empty and negative values."""
    assert _string_or_none("  value ") == "value"
    assert _string_or_none(1) is None
    assert _string_or_none(" ") is None
    assert _int_or_zero(True) == 0
    assert _int_or_zero("bad") == 0
    assert _int_or_zero(-4) == 0
    assert _int_or_zero("3") == EXPECTED_THREE


async def test_storage_load_filters_invalid_records() -> None:
    """Loading should return only valid account records."""
    hass = object()
    with patch("custom_components.ai_usage.storage.Store") as store_class:
        store_class.return_value.async_load = AsyncMock(
            return_value={
                "accounts": [
                    {"provider": "codex", "account_key": "one"},
                    {"provider": "unknown", "account_key": "two"},
                    "invalid",
                ]
            }
        )
        storage = AIUsageStorage(hass, "entry-1")
        accounts = await storage.async_load_accounts()

    assert [account.account_key for account in accounts] == ["one"]


async def test_storage_load_handles_missing_shapes() -> None:
    """Loading should tolerate absent or malformed top-level data."""
    with patch("custom_components.ai_usage.storage.Store") as store_class:
        store_class.return_value.async_load = AsyncMock(return_value=None)
        storage = AIUsageStorage(object(), "entry-1")
        assert await storage.async_load_accounts() == []

        store_class.return_value.async_load = AsyncMock(return_value={"accounts": {}})
        assert await storage.async_load_accounts() == []


async def test_storage_save_sorts_accounts() -> None:
    """Saving should persist a deterministic account order."""
    accounts = [
        AccountState("ollama_cloud", "b", "stable", "B"),
        AccountState("codex", "z", "stable", "Z"),
    ]
    with patch("custom_components.ai_usage.storage.Store") as store_class:
        store_class.return_value.async_save = AsyncMock()
        storage = AIUsageStorage(object(), "entry-1")
        await storage.async_save_accounts(accounts)

    payload = store_class.return_value.async_save.await_args.args[0]
    assert [item["provider"] for item in payload["accounts"]] == [
        "codex",
        "ollama_cloud",
    ]
