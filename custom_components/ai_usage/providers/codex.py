"""Codex provider contract handling."""

from __future__ import annotations

from ..const import PROVIDER_CODEX
from ..models import ProviderMetadata
from .base import ProviderPayloadHandler


class CodexPayloadHandler(ProviderPayloadHandler):
    """Validate Codex usage payloads."""

    provider = PROVIDER_CODEX
    metadata = ProviderMetadata(
        provider=PROVIDER_CODEX,
        provider_name="Codex",
        manufacturer="OpenAI",
        model="Codex account",
        configuration_url="https://chatgpt.com/",
    )
