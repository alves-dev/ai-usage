"""Payload contract validation for AI Usage."""

from __future__ import annotations

from collections.abc import Mapping
from http import HTTPStatus
from typing import Any

from .const import (
    INGEST_STATUS_INVALID_CONTRACT,
    INGEST_STATUS_MISSING_PROVIDER,
    INGEST_STATUS_PAYLOAD_MUST_BE_OBJECT,
    INGEST_STATUS_UNSUPPORTED_PROVIDER,
    KNOWN_COLLECTORS,
    PAYLOAD_SCHEMA_VERSION,
    PROVIDER_STATUS_OK,
    PROVIDER_STATUSES,
    SUPPORTED_PROVIDERS,
)
from .models import PayloadEnvelope, ProviderError
from .providers.base import parse_datetime


class PayloadValidationError(ValueError):
    """Raised when a payload cannot be ingested."""

    def __init__(
        self,
        ingest_status: str,
        message: str,
        *,
        provider: str | None = None,
        http_status: int = HTTPStatus.BAD_REQUEST,
    ) -> None:
        """Initialize the validation error."""
        super().__init__(message)
        self.ingest_status = ingest_status
        self.message = message
        self.provider = provider
        self.http_status = http_status


def validate_payload(payload: object) -> PayloadEnvelope:
    """Validate a raw payload object against the v1 contract."""
    if not isinstance(payload, Mapping):
        raise PayloadValidationError(
            INGEST_STATUS_PAYLOAD_MUST_BE_OBJECT,
            "payload must be an object",
        )

    provider = _validate_provider(payload)
    schema_version = _required_string(payload, "schema_version", provider=provider)
    if schema_version != PAYLOAD_SCHEMA_VERSION:
        raise PayloadValidationError(
            INGEST_STATUS_INVALID_CONTRACT,
            f"schema_version must be {PAYLOAD_SCHEMA_VERSION}",
            provider=provider,
        )

    collector_data = _required_dict(payload, "collector_data", provider=provider)
    collector_id = _required_string(
        collector_data,
        "id",
        provider=provider,
        path="collector_data",
    )
    if collector_id not in KNOWN_COLLECTORS:
        raise PayloadValidationError(
            INGEST_STATUS_INVALID_CONTRACT,
            "collector_data.id is not supported",
            provider=provider,
        )
    collector_version = _required_string(
        collector_data,
        "version",
        provider=provider,
        path="collector_data",
    )
    collected_at_raw = _required_string(payload, "collected_at", provider=provider)
    try:
        collected_at = parse_datetime(collected_at_raw)
    except ValueError as err:
        raise PayloadValidationError(
            INGEST_STATUS_INVALID_CONTRACT,
            "collected_at must be an ISO 8601 datetime with timezone",
            provider=provider,
        ) from err

    status = _required_string(payload, "status", provider=provider)
    if status not in PROVIDER_STATUSES:
        raise PayloadValidationError(
            INGEST_STATUS_INVALID_CONTRACT,
            "status is not supported",
            provider=provider,
        )

    account_data = _required_dict(payload, "account_data", provider=provider)
    plan_data = account_data.get("plan", {})
    if not isinstance(plan_data, Mapping):
        raise PayloadValidationError(
            INGEST_STATUS_INVALID_CONTRACT,
            "account_data.plan must be an object",
            provider=provider,
        )
    usage_data = _required_dict(payload, "usage_data", provider=provider)
    _validate_usage_data(usage_data, status=status, provider=provider)
    if status == PROVIDER_STATUS_OK:
        account_id = account_data.get("id")
        if not isinstance(account_id, str) or not account_id.strip():
            raise PayloadValidationError(
                INGEST_STATUS_INVALID_CONTRACT,
                "account_data.id must be a non-empty string",
                provider=provider,
            )
    error = _validate_error(payload.get("error"), status, provider=provider)

    return PayloadEnvelope(
        schema_version=schema_version,
        source=collector_id,
        source_version=collector_version,
        collected_at=collected_at,
        provider=provider,
        status=status,
        collector_data=collector_data,
        account_data=account_data,
        plan_data=dict(plan_data),
        usage_data=usage_data,
        error=error,
    )


def _validate_provider(payload: Mapping[str, Any]) -> str:
    """Validate and normalize the provider field."""
    provider_raw = payload.get("provider")
    if not isinstance(provider_raw, str) or not provider_raw.strip():
        raise PayloadValidationError(
            INGEST_STATUS_MISSING_PROVIDER,
            "provider must be a non-empty string",
        )

    provider = provider_raw.strip().lower()
    if provider not in SUPPORTED_PROVIDERS:
        raise PayloadValidationError(
            INGEST_STATUS_UNSUPPORTED_PROVIDER,
            "provider is not supported",
            provider=provider,
        )
    return provider


def _required_string(
    payload: Mapping[str, Any],
    key: str,
    *,
    provider: str,
    path: str | None = None,
) -> str:
    """Return a required non-empty string field."""
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PayloadValidationError(
            INGEST_STATUS_INVALID_CONTRACT,
            f"{path or key}.{key} must be a non-empty string"
            if path
            else f"{key} must be a non-empty string",
            provider=provider,
        )
    return value.strip()


def _validate_usage_data(
    usage_data: Mapping[str, Any],
    *,
    status: str,
    provider: str,
) -> None:
    """Validate the common window usage contract."""
    windows = usage_data.get("windows")
    if not isinstance(windows, list):
        raise PayloadValidationError(
            INGEST_STATUS_INVALID_CONTRACT,
            "usage_data.windows must be an array",
            provider=provider,
        )
    if status != PROVIDER_STATUS_OK and not windows:
        return
    if not windows:
        raise PayloadValidationError(
            INGEST_STATUS_INVALID_CONTRACT,
            "usage_data.windows must not be empty",
            provider=provider,
        )
    seen_ids: set[str] = set()
    for index, raw_window in enumerate(windows):
        path = f"usage_data.windows[{index}]"
        if not isinstance(raw_window, Mapping):
            raise PayloadValidationError(
                INGEST_STATUS_INVALID_CONTRACT,
                f"{path} must be an object",
                provider=provider,
            )
        window = dict(raw_window)
        window_id = _window_string(window, "id", path, provider)
        if window_id in seen_ids:
            raise PayloadValidationError(
                INGEST_STATUS_INVALID_CONTRACT,
                f"{path}.id must be unique",
                provider=provider,
            )
        seen_ids.add(window_id)
        _window_string(window, "label", path, provider)
        _window_number(window, "duration_seconds", path, provider, minimum=1)
        _window_number(window, "used_percent", path, provider, maximum=100)
        _window_datetime(window, "reset_at", path, provider)
        limit_reached = window.get("limit_reached")
        if not isinstance(limit_reached, bool):
            raise PayloadValidationError(
                INGEST_STATUS_INVALID_CONTRACT,
                f"{path}.limit_reached must be a boolean",
                provider=provider,
            )
        if "reset_after_seconds" in window:
            _window_number(
                window,
                "reset_after_seconds",
                path,
                provider,
                minimum=0,
            )


def _window_string(
    window: Mapping[str, Any], key: str, path: str, provider: str
) -> str:
    """Validate and return a required window string."""
    value = window.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PayloadValidationError(
            INGEST_STATUS_INVALID_CONTRACT,
            f"{path}.{key} must be a non-empty string",
            provider=provider,
        )
    return value.strip()


def _window_number(
    window: Mapping[str, Any],
    key: str,
    path: str,
    provider: str,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> int | float:
    """Validate a numeric window field."""
    value = window.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PayloadValidationError(
            INGEST_STATUS_INVALID_CONTRACT,
            f"{path}.{key} must be numeric",
            provider=provider,
        )
    if minimum is not None and value < minimum:
        raise PayloadValidationError(
            INGEST_STATUS_INVALID_CONTRACT,
            f"{path}.{key} must be >= {minimum:g}",
            provider=provider,
        )
    if maximum is not None and value > maximum:
        raise PayloadValidationError(
            INGEST_STATUS_INVALID_CONTRACT,
            f"{path}.{key} must be <= {maximum:g}",
            provider=provider,
        )
    return value


def _window_datetime(
    window: Mapping[str, Any], key: str, path: str, provider: str
) -> None:
    """Validate a window ISO datetime field."""
    value = window.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PayloadValidationError(
            INGEST_STATUS_INVALID_CONTRACT,
            f"{path}.{key} must be an ISO 8601 string",
            provider=provider,
        )
    try:
        parse_datetime(value)
    except ValueError as err:
        raise PayloadValidationError(
            INGEST_STATUS_INVALID_CONTRACT,
            f"{path}.{key} must be an ISO 8601 datetime",
            provider=provider,
        ) from err


def _required_dict(
    payload: Mapping[str, Any],
    key: str,
    *,
    provider: str,
) -> dict[str, Any]:
    """Return a required object field as a dict."""
    value = payload.get(key)
    if not isinstance(value, Mapping):
        raise PayloadValidationError(
            INGEST_STATUS_INVALID_CONTRACT,
            f"{key} must be an object",
            provider=provider,
        )
    return dict(value)


def _validate_error(
    value: object,
    status: str,
    *,
    provider: str,
) -> ProviderError | None:
    """Validate the structured provider error."""
    if status == PROVIDER_STATUS_OK:
        if value is not None:
            raise PayloadValidationError(
                INGEST_STATUS_INVALID_CONTRACT,
                "error must be null when status is ok",
                provider=provider,
            )
        return None

    if not isinstance(value, Mapping):
        raise PayloadValidationError(
            INGEST_STATUS_INVALID_CONTRACT,
            "error must be an object when status is not ok",
            provider=provider,
        )

    code = value.get("code")
    message = value.get("message")
    if not isinstance(code, str) or not code.strip():
        raise PayloadValidationError(
            INGEST_STATUS_INVALID_CONTRACT,
            "error.code must be a non-empty string",
            provider=provider,
        )
    if not isinstance(message, str) or not message.strip():
        raise PayloadValidationError(
            INGEST_STATUS_INVALID_CONTRACT,
            "error.message must be a non-empty string",
            provider=provider,
        )

    return ProviderError(code=code.strip(), message=message.strip())
