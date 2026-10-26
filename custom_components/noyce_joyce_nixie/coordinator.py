"""Data coordinator for Noyce Joyce Nixie."""

from __future__ import annotations

import logging
from dataclasses import replace

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import NixieBLE, NixieConnectionError, NixieState
from .const import (
    DATE_TIME_UUID,
    HOURGLASS_UUID,
    NIGHT_MODE_END_UUID,
    NIGHT_MODE_START_UUID,
    NIGHT_MODE_UUID,
    NIXIE_DOTS_UUID,
    TIME_FORMAT_UUID,
    UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class NixieCoordinator(DataUpdateCoordinator[NixieState]):
    """Coordinate BLE reads and writes."""

    def __init__(self, hass, api: NixieBLE) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=api.name,
            update_interval=UPDATE_INTERVAL,
        )
        self.api = api

    async def _async_update_data(self) -> NixieState:
        try:
            return await self.api.async_read_state()
        except NixieConnectionError as err:
            raise UpdateFailed(str(err)) from err

    async def async_set_nixie_dots(self, enabled: bool) -> None:
        await self.api.async_write_u8(NIXIE_DOTS_UUID, int(enabled))
        self.async_set_updated_data(replace(self.data, nixie_dots=enabled))

    async def async_set_night_mode(self, enabled: bool) -> None:
        await self.api.async_write_u8(NIGHT_MODE_UUID, int(enabled))
        self.async_set_updated_data(replace(self.data, night_mode=enabled))

    async def async_set_time_format(self, value: int) -> None:
        if value not in (0, 1):
            raise ValueError("Time format must be 0 or 1")
        await self.api.async_write_u8(TIME_FORMAT_UUID, value)
        self.async_set_updated_data(replace(self.data, time_format=value))

    async def async_set_hourglass(self, value: int) -> None:
        if value not in range(5):
            raise ValueError("Hourglass value must be 0..4")
        await self.api.async_write_u8(HOURGLASS_UUID, value)
        self.async_set_updated_data(replace(self.data, hourglass=value))

    async def async_set_night_start(self, seconds: int) -> None:
        seconds %= 86400
        await self.api.async_write_u32(NIGHT_MODE_START_UUID, seconds)
        self.async_set_updated_data(replace(self.data, night_mode_start=seconds))

    async def async_set_night_end(self, seconds: int) -> None:
        seconds %= 86400
        await self.api.async_write_u32(NIGHT_MODE_END_UUID, seconds)
        self.async_set_updated_data(replace(self.data, night_mode_end=seconds))

    async def async_sync_clock(self) -> None:
        """Synchronize the clock to Home Assistant local wall time.

        The original app sends a Unix-like 32-bit value with the local UTC offset
        added. The firmware converts that value to calendar fields locally.
        """
        from homeassistant.util import dt as dt_util

        now = dt_util.now()
        offset = now.utcoffset()
        offset_seconds = int(offset.total_seconds()) if offset is not None else 0
        local_epoch = int(now.timestamp()) + offset_seconds
        await self.api.async_write_u32(DATE_TIME_UUID, local_epoch)
