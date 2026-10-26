"""Noyce Joyce Nixie Bluetooth integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant

from .api import NoyceJoyceNixie
from .coordinator import NoyceJoyceCoordinator

PLATFORMS: list[Platform] = [
    Platform.SWITCH,
    Platform.SELECT,
    Platform.TIME,
    Platform.SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Noyce Joyce Nixie clock from a config entry."""
    address: str = entry.data[CONF_ADDRESS]
    device = NoyceJoyceNixie(hass, address, entry.title)
    coordinator = NoyceJoyceCoordinator(hass, entry, device)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the integration."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
