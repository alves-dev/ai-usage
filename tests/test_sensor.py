"""Tests for AI Usage sensor descriptions."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from homeassistant.const import UnitOfTime

from custom_components.ai_usage.models import AccountState
from custom_components.ai_usage.sensor import (
    CODEX_SENSOR_DESCRIPTIONS,
    COMMON_ACCOUNT_SENSOR_DESCRIPTIONS,
    INTEGRATION_SENSOR_DESCRIPTIONS,
    OLLAMA_CLOUD_SENSOR_DESCRIPTIONS,
)

EXPECTED_DISABLED_ACCOUNT_SENSOR_KEYS = {
    "collected_at",
    "last_error",
    "last_received_at",
    "request_count",
    "source",
}
EXPECTED_DISABLED_INTEGRATION_SENSOR_KEYS = {
    "last_source",
    "last_unscoped_error",
}
EXPECTED_DISPLAY_PRECISION = 0
EXPECTED_PRIMARY_AVAILABLE_PERCENT = 87.5
EXPECTED_PRIMARY_USED_PERCENT = 12.5
EXPECTED_RESET_AFTER_HOURS = 4
EXPECTED_RESET_AFTER_SECONDS = 14400
EXPECTED_SESSION_AVAILABLE_PERCENT = 92.0
EXPECTED_SESSION_USED_PERCENT = 8.0
EXPECTED_LAST_SAMPLE_AGE_MIN = 29.8
EXPECTED_LAST_SAMPLE_AGE_MAX = 30.2


def test_last_sample_age_is_reported_in_minutes(
    codex_payload: dict[str, Any],
) -> None:
    """Last sample age is derived from the last received timestamp."""
    received_at = datetime.now(UTC) - timedelta(minutes=30)
    state = AccountState(
        provider="codex",
        account_key="acct-test",
        account_key_quality="stable",
        account_label="test@example.com",
        collected_at=datetime(2026, 6, 3, 18, 30, tzinfo=UTC),
        last_received_at=received_at,
        status="ok",
        provider_data=codex_payload["provider_data"],
    )
    description = next(
        item
        for item in COMMON_ACCOUNT_SENSOR_DESCRIPTIONS
        if item.key == "last_sample_age"
    )

    assert description.native_unit_of_measurement == UnitOfTime.MINUTES
    assert description.suggested_display_precision == 1
    assert EXPECTED_LAST_SAMPLE_AGE_MIN <= description.value_fn(state) <= (
        EXPECTED_LAST_SAMPLE_AGE_MAX
    )
    assert (
        description.attributes_fn(state)["last_received_at"]
        == received_at.isoformat()
    )


def test_codex_reset_after_sensors_expose_hours(
    codex_payload: dict[str, Any],
) -> None:
    """Codex reset-after sensor states are hours, not raw payload seconds."""
    state = AccountState(
        provider="codex",
        account_key="acct-test",
        account_key_quality="stable",
        account_label="test@example.com",
        provider_data=codex_payload["provider_data"],
    )
    description = next(
        item
        for item in CODEX_SENSOR_DESCRIPTIONS
        if item.key == "five_hour_usage_reset_after"
    )

    assert description.native_unit_of_measurement == UnitOfTime.HOURS
    assert description.value_fn(state) == EXPECTED_RESET_AFTER_HOURS
    assert (
        description.attributes_fn(state)["reset_after_seconds"]
        == EXPECTED_RESET_AFTER_SECONDS
    )


def test_codex_available_percent_is_derived_from_used_percent(
    codex_payload: dict[str, Any],
) -> None:
    """Codex available percentage is calculated from used percentage."""
    state = AccountState(
        provider="codex",
        account_key="acct-test",
        account_key_quality="stable",
        account_label="test@example.com",
        provider_data=codex_payload["provider_data"],
    )
    description = next(
        item
        for item in CODEX_SENSOR_DESCRIPTIONS
        if item.key == "five_hour_usage_available_percent"
    )

    assert description.suggested_display_precision == EXPECTED_DISPLAY_PRECISION
    assert description.value_fn(state) == EXPECTED_PRIMARY_AVAILABLE_PERCENT
    assert (
        description.attributes_fn(state)["used_percent"]
        == EXPECTED_PRIMARY_USED_PERCENT
    )


def test_ollama_available_percent_is_derived_from_used_percent(
    ollama_payload: dict[str, Any],
) -> None:
    """Ollama Cloud available percentage is calculated from used percentage."""
    state = AccountState(
        provider="ollama_cloud",
        account_key="acct-test",
        account_key_quality="stable",
        account_label="test@example.com",
        provider_data=ollama_payload["provider_data"],
    )
    description = next(
        item
        for item in OLLAMA_CLOUD_SENSOR_DESCRIPTIONS
        if item.key == "session_usage_available_percent"
    )

    assert description.suggested_display_precision == EXPECTED_DISPLAY_PRECISION
    assert description.value_fn(state) == EXPECTED_SESSION_AVAILABLE_PERCENT
    assert (
        description.attributes_fn(state)["used_percent"]
        == EXPECTED_SESSION_USED_PERCENT
    )


def test_low_level_account_diagnostic_sensors_are_disabled_by_default() -> None:
    """Low-level account diagnostics do not clutter new installs by default."""
    disabled_keys = {
        item.key
        for item in COMMON_ACCOUNT_SENSOR_DESCRIPTIONS
        if item.entity_registry_enabled_default is False
    }

    assert disabled_keys == EXPECTED_DISABLED_ACCOUNT_SENSOR_KEYS


def test_low_level_integration_diagnostic_sensors_are_disabled_by_default() -> None:
    """Low-level integration diagnostics do not clutter new installs by default."""
    disabled_keys = {
        item.key
        for item in INTEGRATION_SENSOR_DESCRIPTIONS
        if item.entity_registry_enabled_default is False
    }

    assert disabled_keys == EXPECTED_DISABLED_INTEGRATION_SENSOR_KEYS
