"""Coordinator for the Noyce Joyce Nixie integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import NixieState, NoyceJoyceError, NoyceJoyceNixie
from .const import DOMAIN, UPDATE_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)


class NoyceJoyceCoordinator(DataUpdateCoordinator[NixieState]):
    """Poll the clock without making every entity open its own BLE connection."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        device: NoyceJoyceNixie,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL_SECONDS),
            config_entry=entry,
        )
        self.device = device
        self.entry = entry

    async def _async_update_data(self) -> NixieState:
        try:
            return await self.device.async_read_state()
        except NoyceJoyceError as err:
            raise UpdateFailed(str(err)) from err
