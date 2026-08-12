"""Ollama Cloud provider contract handling."""

from __future__ import annotations

from ..const import PROVIDER_OLLAMA_CLOUD
from ..models import ProviderMetadata
from .base import ProviderPayloadHandler


class OllamaCloudPayloadHandler(ProviderPayloadHandler):
    """Validate Ollama Cloud usage payloads."""

    provider = PROVIDER_OLLAMA_CLOUD
    metadata = ProviderMetadata(
        provider=PROVIDER_OLLAMA_CLOUD,
        provider_name="Ollama Cloud",
        manufacturer="Ollama",
        model="Ollama Cloud account",
        configuration_url="https://ollama.com/settings",
    )
