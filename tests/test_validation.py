"""Tests for AI Usage payload contract validation."""

from __future__ import annotations

from http import HTTPStatus
from typing import Any

from conftest import clone_payload
import pytest

from custom_components.ai_usage.const import (
    INGEST_STATUS_INVALID_CONTRACT,
    INGEST_STATUS_MISSING_PROVIDER,
    INGEST_STATUS_PAYLOAD_MUST_BE_OBJECT,
    INGEST_STATUS_UNSUPPORTED_PROVIDER,
)
from custom_components.ai_usage.validation import (
    PayloadValidationError,
    validate_payload,
)

EXPECTED_WINDOW_COUNT = 2


def _assert_validation_error(
    payload: object,
    ingest_status: str,
    message_fragment: str,
) -> None:
    with pytest.raises(PayloadValidationError) as exc_info:
        validate_payload(payload)
    assert exc_info.value.ingest_status == ingest_status
    assert exc_info.value.http_status == HTTPStatus.BAD_REQUEST
    assert message_fragment in exc_info.value.message


def test_valid_codex_payload(codex_payload: dict[str, Any]) -> None:
    """A valid normalized payload should produce an envelope."""
    envelope = validate_payload(codex_payload)
    assert envelope.provider == "codex"
    assert envelope.source == "manual_test"
    assert envelope.source_version == "1.0.0"
    assert envelope.account_data["id"] == "acct-manual-codex"
    assert len(envelope.usage_data["windows"]) == EXPECTED_WINDOW_COUNT


def test_valid_unknown_provider(codex_payload: dict[str, Any]) -> None:
    """Unknown providers are accepted when the common contract is valid."""
    payload = clone_payload(codex_payload)
    payload["provider"] = "unknown"
    envelope = validate_payload(payload)
    assert envelope.provider == "unknown"


def test_payload_must_be_object() -> None:
    """Payload must be a JSON object."""
    _assert_validation_error(
        [], INGEST_STATUS_PAYLOAD_MUST_BE_OBJECT, "payload must be an object"
    )


def test_missing_provider(codex_payload: dict[str, Any]) -> None:
    """provider is required."""
    payload = clone_payload(codex_payload)
    payload.pop("provider")
    _assert_validation_error(
        payload, INGEST_STATUS_MISSING_PROVIDER, "provider must be a non-empty string"
    )


def test_unsupported_provider(codex_payload: dict[str, Any]) -> None:
    """Unknown arbitrary provider IDs are rejected."""
    payload = clone_payload(codex_payload)
    payload["provider"] = "not_a_supported_provider"
    _assert_validation_error(
        payload, INGEST_STATUS_UNSUPPORTED_PROVIDER, "provider is not supported"
    )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("schema_version", "1.1", "schema_version must be 2.0"),
        ("collector_data", [], "collector_data must be an object"),
        ("account_data", [], "account_data must be an object"),
        ("usage_data", [], "usage_data must be an object"),
    ],
)
def test_invalid_envelope_fields(
    codex_payload: dict[str, Any],
    field: str,
    value: object,
    message: str,
) -> None:
    """Envelope field validation should return invalid_contract."""
    payload = clone_payload(codex_payload)
    payload[field] = value
    _assert_validation_error(payload, INGEST_STATUS_INVALID_CONTRACT, message)


def test_collector_id_must_be_known(codex_payload: dict[str, Any]) -> None:
    """Collectors are explicit and validated independently of providers."""
    payload = clone_payload(codex_payload)
    payload["collector_data"]["id"] = "unknown_collector"
    _assert_validation_error(
        payload,
        INGEST_STATUS_INVALID_CONTRACT,
        "collector_data.id is not supported",
    )


def test_account_id_is_required_for_success(codex_payload: dict[str, Any]) -> None:
    """Successful samples require an explicit stable account ID."""
    payload = clone_payload(codex_payload)
    payload["account_data"].pop("id")
    _assert_validation_error(
        payload,
        INGEST_STATUS_INVALID_CONTRACT,
        "account_data.id must be a non-empty string",
    )


def test_used_percent_must_be_valid(codex_payload: dict[str, Any]) -> None:
    """Window percentages must be between zero and one hundred."""
    payload = clone_payload(codex_payload)
    payload["usage_data"]["windows"][0]["used_percent"] = 101
    _assert_validation_error(
        payload, INGEST_STATUS_INVALID_CONTRACT, "used_percent must be <= 100"
    )


def test_window_label_is_required(codex_payload: dict[str, Any]) -> None:
    """Every window must have a presentation label."""
    payload = clone_payload(codex_payload)
    payload["usage_data"]["windows"][0].pop("label")
    _assert_validation_error(
        payload,
        INGEST_STATUS_INVALID_CONTRACT,
        "label must be a non-empty string",
    )


def test_duplicate_window_ids_are_rejected(codex_payload: dict[str, Any]) -> None:
    """Window IDs must be unique within one sample."""
    payload = clone_payload(codex_payload)
    payload["usage_data"]["windows"][1]["id"] = "short"
    _assert_validation_error(
        payload, INGEST_STATUS_INVALID_CONTRACT, "id must be unique"
    )


def test_reset_at_must_be_iso_datetime(codex_payload: dict[str, Any]) -> None:
    """Window reset timestamps use ISO 8601."""
    payload = clone_payload(codex_payload)
    payload["usage_data"]["windows"][0]["reset_at"] = "not-a-date"
    _assert_validation_error(
        payload,
        INGEST_STATUS_INVALID_CONTRACT,
        "reset_at must be an ISO 8601 datetime",
    )


def test_status_ok_rejects_error(codex_payload: dict[str, Any]) -> None:
    """Successful payloads must not include error."""
    payload = clone_payload(codex_payload)
    payload["error"] = {"code": "unexpected", "message": "Unexpected"}
    _assert_validation_error(
        payload, INGEST_STATUS_INVALID_CONTRACT, "error must be null"
    )


def test_error_status_allows_empty_usage(error_payload: dict[str, Any]) -> None:
    """Error payloads can be unscoped and contain no windows."""
    envelope = validate_payload(error_payload)
    assert envelope.status == "not_authenticated"
    assert envelope.usage_data == {"windows": []}
