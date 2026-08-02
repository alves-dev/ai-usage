"""Tests for the AI Usage config flow helpers."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from custom_components.ai_usage.config_flow import (
    AIUsageConfigFlow,
    _clean_webhook_id,
    _webhook_schema,
)
from custom_components.ai_usage.const import CONF_WEBHOOK_ID


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("  webhook_123  ", "webhook_123"),
        ("a" * 8, "a" * 8),
        ("a" * 128, "a" * 128),
        (None, None),
        (123, None),
        ("short", None),
        ("has spaces", None),
        ("has/slash", None),
        ("a" * 129, None),
    ],
)
def test_clean_webhook_id(value: object, expected: str | None) -> None:
    """Webhook IDs should be normalized and constrained to safe characters."""
    assert _clean_webhook_id(value) == expected


def test_webhook_schema_requires_id() -> None:
    """The schema should expose the configured default value."""
    schema = _webhook_schema("webhook_123")
    assert schema({CONF_WEBHOOK_ID: "webhook_123"})[CONF_WEBHOOK_ID] == "webhook_123"


async def test_user_step_shows_form_with_generated_default() -> None:
    """The initial step should generate and retain a default webhook ID."""
    flow = AIUsageConfigFlow()
    flow.async_set_unique_id = AsyncMock()
    flow._abort_if_unique_id_configured = lambda: None

    with patch(
        "custom_components.ai_usage.config_flow.webhook.async_generate_id",
        return_value="generated_id",
    ):
        result = await flow.async_step_user()
        second_result = await flow.async_step_user()

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {}
    assert result["data_schema"]({CONF_WEBHOOK_ID: "generated_id"})[CONF_WEBHOOK_ID]
    assert second_result["data_schema"]({CONF_WEBHOOK_ID: "generated_id"})[
        CONF_WEBHOOK_ID
    ]
    flow.async_set_unique_id.assert_any_await("ai_usage")


async def test_user_step_rejects_invalid_and_accepts_valid_id() -> None:
    """The initial step should report invalid IDs and create valid entries."""
    flow = AIUsageConfigFlow()
    flow.async_set_unique_id = AsyncMock()
    flow._abort_if_unique_id_configured = lambda: None

    invalid = await flow.async_step_user({CONF_WEBHOOK_ID: "bad"})
    assert invalid["errors"] == {CONF_WEBHOOK_ID: "invalid_webhook_id"}

    flow.async_create_entry = lambda **kwargs: kwargs
    valid = await flow.async_step_user({CONF_WEBHOOK_ID: " valid_id "})
    assert valid == {
        "title": "AI Usage",
        "data": {CONF_WEBHOOK_ID: "valid_id"},
    }


async def test_reconfigure_step_updates_entry_and_reports_errors() -> None:
    """Reconfiguration should preserve the form default and update valid IDs."""
    flow = AIUsageConfigFlow()
    entry = SimpleNamespace(data={CONF_WEBHOOK_ID: "old_webhook"})
    flow._get_reconfigure_entry = lambda: entry
    flow.async_set_unique_id = AsyncMock()
    flow._abort_if_unique_id_mismatch = lambda: None

    invalid = await flow.async_step_reconfigure({CONF_WEBHOOK_ID: "bad"})
    assert invalid["step_id"] == "reconfigure"
    assert invalid["errors"] == {CONF_WEBHOOK_ID: "invalid_webhook_id"}

    flow.async_update_reload_and_abort = lambda current, **kwargs: {
        "entry": current,
        **kwargs,
    }
    valid = await flow.async_step_reconfigure({CONF_WEBHOOK_ID: "new_webhook"})
    assert valid["entry"] is entry
    assert valid["data_updates"] == {CONF_WEBHOOK_ID: "new_webhook"}
