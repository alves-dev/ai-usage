"""Tests for provider image registration."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from custom_components.ai_usage.images import (
    async_register_provider_static_paths,
    provider_entity_picture,
)


async def test_register_provider_images_once() -> None:
    """Existing provider images should be registered only once."""
    hass = SimpleNamespace(
        data={},
        http=SimpleNamespace(async_register_static_paths=AsyncMock()),
        async_add_executor_job=AsyncMock(side_effect=lambda function: function()),
    )

    await async_register_provider_static_paths(hass)
    await async_register_provider_static_paths(hass)

    hass.http.async_register_static_paths.assert_awaited_once()
    assert provider_entity_picture(hass, "codex") is not None
    assert provider_entity_picture(hass, "unknown") is None


async def test_register_provider_images_handles_missing_files() -> None:
    """Missing image files should not prevent registration from completing."""
    hass = SimpleNamespace(
        data={},
        http=SimpleNamespace(async_register_static_paths=AsyncMock()),
        async_add_executor_job=AsyncMock(side_effect=lambda function: function()),
    )
    with patch(
        "custom_components.ai_usage.images.PROVIDER_IMAGE_FILES",
        {"codex": "missing.png"},
    ):
        await async_register_provider_static_paths(hass)

    assert provider_entity_picture(hass, "codex") is None
    hass.http.async_register_static_paths.assert_not_awaited()
    assert provider_entity_picture(SimpleNamespace(data={}), "codex") is None
