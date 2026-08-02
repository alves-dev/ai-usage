"""Tests for AI Usage runtime state and webhook handling."""

from __future__ import annotations

from datetime import UTC, datetime
from http import HTTPStatus
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from custom_components.ai_usage.const import INGEST_STATUS_INVALID_JSON
from custom_components.ai_usage.models import AccountIdentity, IngestContext
from custom_components.ai_usage.runtime import AIUsageRuntime, _metadata_compare
from custom_components.ai_usage.validation import validate_payload


class FakeBus:
    """Capture Home Assistant events."""

    def __init__(self) -> None:
        self.events: list[tuple[str, dict]] = []

    def async_fire(self, event: str, data: dict) -> None:
        self.events.append((event, data))


EXPECTED_APPLY_DISPATCHES = 3


def _hass() -> SimpleNamespace:
    return SimpleNamespace(data={}, bus=FakeBus())


def _entry() -> SimpleNamespace:
    return SimpleNamespace(entry_id="entry-1", title="AI Usage")


def _runtime_instance(hass: SimpleNamespace) -> AIUsageRuntime:
    with patch("custom_components.ai_usage.runtime.AIUsageStorage") as storage_class:
        runtime = AIUsageRuntime(hass, _entry())
    runtime._storage = storage_class.return_value
    return runtime


def test_runtime_account_callbacks_and_metadata() -> None:
    """Runtime should register callbacks and compare only persisted metadata."""
    account = SimpleNamespace(
        persisted_metadata=lambda: {
            "provider": "codex",
            "request_count": 4,
            "last_seen_at": "now",
            "account_label": "Test",
        }
    )
    assert _metadata_compare(None) is None
    assert _metadata_compare(account) == {"provider": "codex", "account_label": "Test"}


async def test_runtime_setup_loads_accounts_and_registers_images() -> None:
    """Runtime setup should load persisted accounts before platform setup."""
    hass = _hass()
    entry = _entry()
    with patch("custom_components.ai_usage.runtime.AIUsageStorage") as storage_class:
        account = SimpleNamespace(provider="codex", account_key="acct-1")
        storage_class.return_value.async_load_accounts = AsyncMock(
            return_value=[account]
        )
        with patch(
            "custom_components.ai_usage.runtime.async_register_provider_static_paths",
            new=AsyncMock(),
        ) as register_paths:
            runtime = AIUsageRuntime(hass, entry)
            await runtime.async_setup()

    register_paths.assert_awaited_once_with(hass)
    assert runtime.account_states == (account,)
    assert runtime.integration_state.known_accounts == 1
    assert runtime.integration_state.known_accounts_by_provider == {"codex": 1}


async def test_runtime_apply_sample_notifies_and_saves(codex_payload: dict) -> None:
    """A new account should be saved and notify both platform callback types."""
    hass = _hass()
    runtime = _runtime_instance(hass)
    runtime._storage.async_save_accounts = AsyncMock()
    sensor_accounts: list[object] = []
    binary_accounts: list[object] = []
    runtime.async_register_account_sensor_callback(sensor_accounts.append)
    runtime.async_register_account_binary_sensor_callback(binary_accounts.append)
    envelope = validate_payload(codex_payload)
    identity = AccountIdentity(
        provider="codex",
        account_key="acct-test",
        account_key_quality="stable",
        id_kind="account_id",
        id_value="acct-test",
        label="Test",
    )
    context = IngestContext("test", datetime(2026, 6, 3, tzinfo=UTC))

    with patch("custom_components.ai_usage.runtime.async_dispatcher_send") as send:
        created = await runtime.async_apply_account_sample(envelope, identity, context)

    assert created is True
    assert len(sensor_accounts) == 1
    assert len(binary_accounts) == 1
    assert runtime.get_account_state("codex", "acct-test").request_count == 1
    runtime._storage.async_save_accounts.assert_awaited_once()
    assert send.call_count == EXPECTED_APPLY_DISPATCHES


async def test_runtime_records_results_and_unscoped_errors(error_payload: dict) -> None:
    """Runtime should update integration diagnostics for errors."""
    hass = _hass()
    runtime = _runtime_instance(hass)
    envelope = validate_payload(error_payload)
    received_at = datetime(2026, 6, 3, tzinfo=UTC)
    context = IngestContext("webhook", received_at, "webhook-1", "127.0.0.1")

    await runtime.async_record_unscoped_error(
        envelope,
        context,
        error_code="not_authenticated",
        message="Not authenticated",
    )
    assert runtime.integration_state.last_unscoped_error == "not_authenticated"
    assert runtime.integration_state.last_unscoped_error_provider == "codex"

    result = SimpleNamespace(
        ingest_status="account_unidentified",
        message="Not authenticated",
        provider="codex",
        account_key=None,
        provider_status="not_authenticated",
        created_account=False,
    )
    with patch("custom_components.ai_usage.runtime.async_dispatcher_send") as send:
        await runtime.async_record_ingest_result(result, context, envelope)

    state = runtime.integration_state
    assert state.last_webhook_received_at == received_at
    assert state.last_source == envelope.source
    assert state.last_provider == "codex"
    assert hass.bus.events[0][1]["ingest_status"] == "account_unidentified"
    send.assert_called_once()


async def test_runtime_webhook_returns_bad_request_for_invalid_json() -> None:
    """Invalid JSON should return the documented webhook response."""
    hass = _hass()
    runtime = _runtime_instance(hass)
    request = SimpleNamespace(
        remote="127.0.0.1",
        json=AsyncMock(side_effect=ValueError()),
    )

    with patch("custom_components.ai_usage.runtime.async_dispatcher_send"):
        response = await runtime.async_handle_webhook(
            hass,
            "webhook-1",
            request,  # type: ignore[arg-type]
        )

    assert response.status == HTTPStatus.BAD_REQUEST
    assert response.text is not None
    assert INGEST_STATUS_INVALID_JSON in response.text


async def test_runtime_webhook_delegates_valid_payload(
    codex_payload: dict,
) -> None:
    """Valid webhook requests should delegate to the ingestion service."""
    hass = _hass()
    runtime = _runtime_instance(hass)
    runtime.ingestion_service.async_ingest_payload = AsyncMock(
        return_value=SimpleNamespace(
            as_response=lambda: {"ok": True},
            http_status=HTTPStatus.OK,
        )
    )
    request = SimpleNamespace(
        remote="127.0.0.1",
        json=AsyncMock(return_value=codex_payload),
    )

    response = await runtime.async_handle_webhook(
        hass,
        "webhook-1",
        request,  # type: ignore[arg-type]
    )

    assert response.status == HTTPStatus.OK
    runtime.ingestion_service.async_ingest_payload.assert_awaited_once()


async def test_runtime_unload_clears_callbacks() -> None:
    """Unloading should release platform callback references."""
    runtime = _runtime_instance(_hass())
    runtime._account_sensor_callbacks.append(lambda _account: None)
    runtime._account_binary_sensor_callbacks.append(lambda _account: None)
    await runtime.async_unload()
    assert runtime._account_sensor_callbacks == []
    assert runtime._account_binary_sensor_callbacks == []
