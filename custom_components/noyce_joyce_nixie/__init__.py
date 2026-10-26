"""Noyce Joyce Nixie Clock integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant

from .api import NixieBLE
from .const import DOMAIN, NAME
from .coordinator import NixieCoordinator

PLATFORMS: list[Platform] = [
    Platform.SWITCH,
    Platform.SELECT,
    Platform.TIME,
    Platform.BUTTON,
    Platform.SENSOR,
]

type NixieConfigEntry = ConfigEntry[NixieCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: NixieConfigEntry) -> bool:
    """Set up Noyce Joyce Nixie from a config entry."""
    address = entry.data[CONF_ADDRESS]
    api = NixieBLE(hass, address, entry.title or NAME)
    coordinator = NixieCoordinator(hass, api, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    coordinator.async_start()
    return True


async def async_unload_entry(hass: HomeAssistant, entry: NixieConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        entry.runtime_data.async_shutdown()
    return unload_ok
