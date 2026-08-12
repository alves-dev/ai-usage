"""Register the AI Usage Lovelace card with Home Assistant."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components import frontend
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import DOMAIN

CARD_URL = f"/api/{DOMAIN}/lovelace/ai-usage-windows-card.js"
_CARD_REGISTERED = "_lovelace_card_registered"


async def async_register_card(hass: HomeAssistant) -> None:
    """Serve and register the custom card as a frontend extra module."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get(_CARD_REGISTERED):
        return

    card_path = Path(__file__).parent / "lovelace" / "ai-usage-windows-card.js"
    if not card_path.is_file():
        return

    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(card_path), cache_headers=False)]
    )
    frontend.add_extra_js_url(hass, CARD_URL)
    domain_data[_CARD_REGISTERED] = True
