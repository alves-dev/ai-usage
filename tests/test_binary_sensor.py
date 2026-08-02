"""Tests for AI Usage binary sensor descriptions and entities."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN

from custom_components.ai_usage.binary_sensor import (
    COMMON_ACCOUNT_BINARY_SENSOR_DESCRIPTIONS,
    INTEGRATION_BINARY_SENSOR_DESCRIPTIONS,
    AIUsageAccountBinarySensor,
    AIUsageIntegrationBinarySensor,
    _account_binary_sensor_descriptions,
    _account_device_info,
    _codex_rate_limit_bool,
    _codex_window_number,
    _drop_none,
    _integration_device_info,
    _restore_binary_value,
)
from custom_components.ai_usage.const import DOMAIN, INGEST_STATUS_OK
from custom_components.ai_usage.models import (
    AccountState,
    IntegrationState,
    ProviderMetadata,
)

EXPECTED_CODEX_BINARY_SENSORS = 3


def _entry() -> SimpleNamespace:
    return SimpleNamespace(entry_id="entry-1", title="AI Usage")


def _runtime(account: AccountState) -> SimpleNamespace:
    return SimpleNamespace(
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


def test_binary_sensor_helpers_handle_valid_and_invalid_values() -> None:
    """Nested binary sensor values should reject malformed types."""
    state = AccountState(
        provider="codex",
        account_key="acct-test",
        account_key_quality="stable",
        account_label="Test",
        provider_data={"rate_limit": {"allowed": True, "used": 12.5}},
    )
    assert _codex_rate_limit_bool(state, "allowed") is True
    assert _codex_rate_limit_bool(state, "missing") is None
    assert _codex_window_number(state, "rate_limit", "used") is None
    assert _codex_window_number(state, "five_hour_window", "used") is None
    assert _drop_none({"a": 1, "b": None}) == {"a": 1}


def test_description_selection_and_device_info() -> None:
    """Provider descriptions should include common and enabled provider sensors."""
    assert (
        len(_account_binary_sensor_descriptions("codex"))
        == EXPECTED_CODEX_BINARY_SENSORS
    )
    assert len(_account_binary_sensor_descriptions("ollama_cloud")) == 1
    assert len(_account_binary_sensor_descriptions("unknown")) == 1

    entry = _entry()
    integration_info = _integration_device_info(entry)
    assert integration_info["identifiers"] == {(DOMAIN, "entry-1")}
    assert integration_info["name"] == "Source Webhook"

    account = AccountState("codex", "acct-test", "stable", "Test")
    account_info = _account_device_info(entry, _runtime(account), account)
    assert account_info["name"] == "Codex Test"
    assert account_info["via_device"] == (DOMAIN, "entry-1")


def test_integration_binary_sensor_reads_state_and_attributes() -> None:
    """Integration entities should expose their runtime state."""
    runtime = _runtime(AccountState("codex", "acct-test", "stable", "Test"))
    description = INTEGRATION_BINARY_SENSOR_DESCRIPTIONS[0]
    entity = AIUsageIntegrationBinarySensor(_entry(), runtime, description)

    assert entity.unique_id == "entry-1:webhook_problem"
    assert entity.is_on is False
    assert entity.extra_state_attributes == {"last_ingest_status": "ok"}

    runtime.integration_state.last_ingest_status = "invalid_contract"
    runtime.integration_state.last_ingest_error_message = "bad payload"
    assert entity.is_on is True
    assert entity.extra_state_attributes == {
        "last_ingest_status": "invalid_contract",
        "last_error_message": "bad payload",
    }


def test_account_binary_sensor_reads_live_and_restored_state() -> None:
    """Account entities should prefer live values and fall back to restored ones."""
    account = AccountState(
        "codex",
        "acct-test",
        "stable",
        "Test",
        provider_data={"rate_limit": {"allowed": True}},
    )
    runtime = _runtime(account)
    description = COMMON_ACCOUNT_BINARY_SENSOR_DESCRIPTIONS[0]
    entity = AIUsageAccountBinarySensor(_entry(), runtime, account, description)

    assert entity.unique_id == "entry-1:codex:acct-test:problem"
    assert entity.is_on is None
    assert entity.extra_state_attributes is None

    account.status = INGEST_STATUS_OK
    account.last_received_at = datetime.now(UTC)
    assert entity.is_on is False
    assert entity.extra_state_attributes == {"status": INGEST_STATUS_OK}
    assert entity.device_info["name"] == "Codex Test"


def test_restore_binary_value() -> None:
    """Home Assistant state strings should map to native binary values."""
    assert _restore_binary_value(STATE_ON) is True
    assert _restore_binary_value(STATE_OFF) is False
    assert _restore_binary_value(STATE_UNKNOWN) is None
    assert _restore_binary_value(STATE_UNAVAILABLE) is None
    assert _restore_binary_value("unexpected") is None
