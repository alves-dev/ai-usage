"""Tests for AI Usage sensor descriptions."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from homeassistant.const import UnitOfTime

from custom_components.ai_usage.models import AccountState, IntegrationState
from custom_components.ai_usage.sensor import (
    COMMON_ACCOUNT_SENSOR_DESCRIPTIONS,
    INTEGRATION_SENSOR_DESCRIPTIONS,
    _account_sensor_descriptions,
)

AGE_MINUTES_LOWER = 29.8
AGE_MINUTES_UPPER = 30.2
SHORT_USED_PERCENT = 12.5
SHORT_AVAILABLE_PERCENT = 87.5
EXPECTED_WINDOW_COUNT = 2


def _state(codex_payload: dict[str, Any]) -> AccountState:
    return AccountState(
        provider="codex",
        account_key="acct-test",
        account_key_quality="stable",
        account_label="Test",
        usage_data=codex_payload["usage_data"],
        status="ok",
        last_received_at=datetime.now(UTC),
    )


def test_last_sample_age_is_reported_in_minutes(
    codex_payload: dict[str, Any],
) -> None:
    """Last sample age is derived from the last received timestamp."""
    received_at = datetime.now(UTC) - timedelta(minutes=30)
    state = _state(codex_payload)
    state.last_received_at = received_at
    description = next(
        item
        for item in COMMON_ACCOUNT_SENSOR_DESCRIPTIONS
        if item.key == "last_sample_age"
    )
    assert description.native_unit_of_measurement == UnitOfTime.MINUTES
    assert AGE_MINUTES_LOWER <= description.value_fn(state) <= AGE_MINUTES_UPPER


def test_window_sensors_use_stable_window_id_and_derive_available(
    codex_payload: dict[str, Any],
) -> None:
    """Each window creates used, available and reset sensors."""
    state = _state(codex_payload)
    descriptions = _account_sensor_descriptions(state)
    available = next(
        item for item in descriptions if item.key == "window_short_available_percent"
    )
    used = next(
        item for item in descriptions if item.key == "window_short_used_percent"
    )
    reset = next(item for item in descriptions if item.key == "window_short_reset_at")
    assert used.value_fn(state) == SHORT_USED_PERCENT
    assert available.value_fn(state) == SHORT_AVAILABLE_PERCENT
    assert reset.value_fn(state) == datetime(2026, 6, 3, 22, 30, tzinfo=UTC)
    assert available.attributes_fn(state)["used_percent"] == SHORT_USED_PERCENT


def test_new_window_is_supported_without_provider_code(
    codex_payload: dict[str, Any],
) -> None:
    """A third window produces the same generic sensor set."""
    payload = dict(codex_payload["usage_data"])
    payload["windows"] = [
        *payload["windows"],
        {
            "id": "daily",
            "label": "Daily window",
            "duration_seconds": 86400,
            "used_percent": 50,
            "reset_at": "2026-06-04T00:00:00Z",
            "limit_reached": True,
        },
    ]
    state = _state(codex_payload)
    state.usage_data = payload
    keys = {description.key for description in _account_sensor_descriptions(state)}
    assert "window_daily_used_percent" in keys
    assert "window_daily_available_percent" in keys


def test_low_level_diagnostic_sensors_are_disabled_by_default() -> None:
    """Low-level account diagnostics do not clutter new installs."""
    disabled = {
        item.key
        for item in COMMON_ACCOUNT_SENSOR_DESCRIPTIONS
        if item.entity_registry_enabled_default is False
    }
    assert disabled == {
        "collected_at",
        "last_error",
        "last_received_at",
        "request_count",
        "source",
    }


def test_low_level_integration_sensors_are_disabled_by_default() -> None:
    """Low-level integration diagnostics are disabled by default."""
    disabled = {
        item.key
        for item in INTEGRATION_SENSOR_DESCRIPTIONS
        if item.entity_registry_enabled_default is False
    }
    assert disabled == {"last_source", "last_unscoped_error"}


def test_ingest_status_attributes_do_not_expose_webhook_id() -> None:
    """Webhook IDs must not be published as state attributes."""
    description = next(
        item
        for item in INTEGRATION_SENSOR_DESCRIPTIONS
        if item.key == "last_ingest_status"
    )
    assert "webhook_id" not in description.attributes_fn(IntegrationState())
