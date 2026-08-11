"""Tests for AI Usage account identity resolution."""

from __future__ import annotations

import hashlib

from custom_components.ai_usage.identity import (
    normalize_email,
    resolve_account_identity,
)


def _expected_account_key(provider: str, id_kind: str, id_value: str) -> str:
    digest = hashlib.sha256(f"{provider}:{id_kind}:{id_value}".encode()).hexdigest()
    return f"acct_{digest[:16]}"


def test_explicit_account_id_is_used() -> None:
    """The normalized account ID is the only identity source."""
    identity = resolve_account_identity(
        "codex",
        {"id": "acct-123", "email": "user@example.com", "label": "Personal"},
    )
    assert identity is not None
    assert identity.id_kind == "account_id"
    assert identity.id_value == "acct-123"
    assert identity.account_key_quality == "stable"
    assert identity.account_key == _expected_account_key(
        "codex", "account_id", "acct-123"
    )
    assert identity.label == "user@example.com"


def test_missing_explicit_id_does_not_identify_account() -> None:
    """Email and username are not identity fallbacks in contract 2.0."""
    assert (
        resolve_account_identity("ollama_cloud", {"email": "user@example.com"}) is None
    )
    assert resolve_account_identity("ollama_cloud", {"username": "igor"}) is None


def test_normalize_email_remains_available_for_legacy_helpers() -> None:
    """Email normalization remains useful to collectors without being identity."""
    assert normalize_email(" User@Example.COM ") == "user@example.com"
    assert normalize_email(None) is None
    assert normalize_email("   ") is None
