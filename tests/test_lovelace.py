"""Tests for the bundled Lovelace card registration."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from custom_components.ai_usage.lovelace import CARD_URL, async_register_card


async def test_register_card_serves_and_registers_frontend_module() -> None:
    """The card should be registered once as a frontend extra module."""
    hass = SimpleNamespace(
        data={},
        http=SimpleNamespace(async_register_static_paths=AsyncMock()),
    )

    with patch("custom_components.ai_usage.lovelace.frontend.add_extra_js_url") as add:
        await async_register_card(hass)
        await async_register_card(hass)

    hass.http.async_register_static_paths.assert_awaited_once()
    add.assert_called_once_with(hass, CARD_URL)
    assert hass.data["ai_usage"]["_lovelace_card_registered"] is True


async def test_register_card_ignores_missing_bundle() -> None:
    """A missing frontend asset should not prevent integration setup."""
    hass = SimpleNamespace(
        data={},
        http=SimpleNamespace(async_register_static_paths=AsyncMock()),
    )

    with patch("custom_components.ai_usage.lovelace.Path.is_file", return_value=False):
        await async_register_card(hass)

    hass.http.async_register_static_paths.assert_not_awaited()
