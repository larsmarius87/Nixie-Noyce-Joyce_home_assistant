"""Noyce Joyce Nixie Bluetooth integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_change

from .api import NoyceJoyceError, NoyceJoyceNixie
from .coordinator import NoyceJoyceCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SWITCH,
    Platform.SELECT,
    Platform.TIME,
    Platform.SENSOR,
    Platform.BUTTON,
]

# Synchronize after the European DST transition window and at a quiet time.
DAILY_SYNC_HOUR = 4
DAILY_SYNC_MINUTE = 5


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Noyce Joyce Nixie clock from a config entry."""
    address: str = entry.data[CONF_ADDRESS]
    device = NoyceJoyceNixie(hass, address, entry.title)
    coordinator = NoyceJoyceCoordinator(hass, entry, device)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def _async_daily_time_sync(_now) -> None:
        try:
            await coordinator.async_sync_clock()
        except NoyceJoyceError as err:
            # A missed sync is non-fatal; the next daily run will try again.
            _LOGGER.warning("Daily time sync failed for %s: %s", entry.title, err)

    entry.async_on_unload(
        async_track_time_change(
            hass,
            _async_daily_time_sync,
            hour=DAILY_SYNC_HOUR,
            minute=DAILY_SYNC_MINUTE,
            second=0,
        )
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the integration."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
