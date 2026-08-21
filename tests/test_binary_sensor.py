"""Tests for AI Usage binary sensor descriptions and entities."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import patch

from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN

from custom_components.ai_usage.binary_sensor import (
    COMMON_ACCOUNT_BINARY_SENSOR_DESCRIPTIONS,
    INTEGRATION_BINARY_SENSOR_DESCRIPTIONS,
    AIUsageAccountBinarySensor,
    AIUsageIntegrationBinarySensor,
    _account_binary_sensor_descriptions,
    _account_device_info,
    _integration_device_info,
    _restore_binary_value,
)
from custom_components.ai_usage.const import DOMAIN, INGEST_STATUS_OK
from custom_components.ai_usage.models import (
    AccountState,
    IntegrationState,
    ProviderMetadata,
)


def _entry() -> SimpleNamespace:
    return SimpleNamespace(entry_id="entry-1", title="AI Usage", data={})


def _runtime(account: AccountState) -> SimpleNamespace:
    return SimpleNamespace(
        hass=SimpleNamespace(),
        integration_state=IntegrationState(),
        get_account_state=lambda _provider, _key: account,
        get_provider_metadata=lambda _provider: ProviderMetadata(
            provider="codex",
            provider_name="Codex",
            manufacturer="OpenAI",
            model="Codex",
            configuration_url="https://example.com",
        ),
    )


def test_dynamic_binary_sensors_include_available_and_each_window(
    codex_payload: dict,
) -> None:
    """The common available sensor and window limit sensors are generated."""
    account = AccountState(
        "codex", "acct-test", "stable", "Test", usage_data=codex_payload["usage_data"]
    )
    descriptions = _account_binary_sensor_descriptions(account)
    keys = {description.key for description in descriptions}
    assert "available" in keys
    assert "window_short_limit_reached" in keys
    available = next(item for item in descriptions if item.key == "available")
    account.status = "ok"
    account.last_received_at = datetime.now(UTC)
    assert available.value_fn(account) is True

    account.usage_data["windows"][0]["limit_reached"] = True
    account.usage_data["windows"][1]["limit_reached"] = True
    assert available.value_fn(account) is False


def test_account_binary_sensor_reads_live_and_restored_state() -> None:
    """Account entities prefer live values and fall back to restored ones."""
    account = AccountState("codex", "acct-test", "stable", "Test")
    runtime = _runtime(account)
    description = COMMON_ACCOUNT_BINARY_SENSOR_DESCRIPTIONS[0]
    entity = AIUsageAccountBinarySensor(_entry(), runtime, account, description)
    assert entity.unique_id == "entry-1:codex:acct-test:problem"
    assert entity.is_on is None
    account.status = INGEST_STATUS_OK
    account.last_received_at = datetime.now(UTC)
    assert entity.is_on is False
    assert entity.extra_state_attributes == {"status": INGEST_STATUS_OK}


def test_integration_binary_sensor_reads_state() -> None:
    """The webhook problem entity reads integration state."""
    runtime = _runtime(AccountState("codex", "acct-test", "stable", "Test"))
    entity = AIUsageIntegrationBinarySensor(
        _entry(), runtime, INTEGRATION_BINARY_SENSOR_DESCRIPTIONS[0]
    )
    assert entity.unique_id == "entry-1:webhook_problem"
    assert entity.is_on is False
    runtime.integration_state.last_ingest_status = "invalid_contract"
    assert entity.is_on is True


def test_device_info_helpers() -> None:
    """Parent and account devices have stable identifiers."""
    entry = _entry()
    assert _integration_device_info(entry)["identifiers"] == {(DOMAIN, "entry-1")}
    account = AccountState("codex", "acct-test", "stable", "Test")
    runtime = _runtime(account)
    parent = SimpleNamespace(id="parent-device-id")
    registry = SimpleNamespace(
        async_get_device=lambda *, identifiers: parent,
    )
    with patch(
        "custom_components.ai_usage.binary_sensor.device_registry.async_get",
        return_value=registry,
    ):
        info = _account_device_info(entry, runtime, account)
    assert info["name"] == "Test"
    assert info["via_device_id"] == "parent-device-id"


def test_restore_binary_value() -> None:
    """Restored HA state strings map to native booleans."""
    assert _restore_binary_value(STATE_ON) is True
    assert _restore_binary_value(STATE_OFF) is False
    assert _restore_binary_value(STATE_UNKNOWN) is None
    assert _restore_binary_value(STATE_UNAVAILABLE) is None
