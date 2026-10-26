"""Data coordinator for Noyce Joyce Nixie."""

from __future__ import annotations

import logging
from dataclasses import replace
from datetime import datetime, time, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import NixieBLE, NixieConnectionError, NixieState
from .const import (
    CONF_AUTO_SYNC_ENABLED,
    CONF_AUTO_SYNC_TIME,
    DATE_TIME_UUID,
    DEFAULT_AUTO_SYNC_ENABLED,
    DEFAULT_AUTO_SYNC_TIME,
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

    def __init__(self, hass, api: NixieBLE, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=api.name,
            update_interval=UPDATE_INTERVAL,
        )
        self.api = api
        self.entry = entry
        self._unsub_auto_sync = None

    async def _async_update_data(self) -> NixieState:
        try:
            return await self.api.async_read_state()
        except NixieConnectionError as err:
            raise UpdateFailed(str(err)) from err

    @property
    def auto_sync_enabled(self) -> bool:
        """Return whether daily automatic clock synchronization is enabled."""
        return bool(
            self.entry.options.get(CONF_AUTO_SYNC_ENABLED, DEFAULT_AUTO_SYNC_ENABLED)
        )

    @property
    def auto_sync_time(self) -> time:
        """Return configured daily automatic synchronization time."""
        raw_value = self.entry.options.get(CONF_AUTO_SYNC_TIME, DEFAULT_AUTO_SYNC_TIME)
        try:
            value = time.fromisoformat(str(raw_value))
        except ValueError:
            value = time.fromisoformat(DEFAULT_AUTO_SYNC_TIME)
        return value.replace(tzinfo=None)

    @callback
    def async_start_auto_sync(self) -> None:
        """Start or reschedule the daily automatic synchronization timer."""
        self._schedule_auto_sync()

    @callback
    def async_shutdown(self) -> None:
        """Cancel the automatic synchronization timer."""
        if self._unsub_auto_sync is not None:
            self._unsub_auto_sync()
            self._unsub_auto_sync = None

    @callback
    def _schedule_auto_sync(self) -> None:
        """Schedule the next automatic synchronization in HA local time."""
        if self._unsub_auto_sync is not None:
            self._unsub_auto_sync()
            self._unsub_auto_sync = None

        if not self.auto_sync_enabled:
            return

        now = dt_util.now()
        next_run = datetime.combine(
            now.date(),
            self.auto_sync_time,
            tzinfo=now.tzinfo,
        )
        if next_run <= now:
            next_run = datetime.combine(
                now.date() + timedelta(days=1),
                self.auto_sync_time,
                tzinfo=now.tzinfo,
            )

        _LOGGER.debug("Next Nixie automatic clock sync scheduled for %s", next_run)
        self._unsub_auto_sync = async_track_point_in_time(
            self.hass,
            self._handle_auto_sync,
            next_run,
        )

    @callback
    def _handle_auto_sync(self, _now: datetime) -> None:
        """Handle the scheduled automatic synchronization callback."""
        self._unsub_auto_sync = None
        self.hass.async_create_task(self._async_auto_sync_and_reschedule())

    async def _async_auto_sync_and_reschedule(self) -> None:
        """Synchronize the clock, then schedule the next daily run."""
        try:
            await self.async_sync_clock()
            _LOGGER.debug("Automatic Nixie clock synchronization completed")
        except NixieConnectionError:
            _LOGGER.warning(
                "Automatic Nixie clock synchronization failed; will try again at the next scheduled time",
                exc_info=True,
            )
        finally:
            self._schedule_auto_sync()

    async def async_set_auto_sync_enabled(self, enabled: bool) -> None:
        """Persist and apply automatic synchronization enabled state."""
        options = dict(self.entry.options)
        options[CONF_AUTO_SYNC_ENABLED] = bool(enabled)
        self.hass.config_entries.async_update_entry(self.entry, options=options)
        self._schedule_auto_sync()
        self.async_update_listeners()

    async def async_set_auto_sync_time(self, value: time) -> None:
        """Persist and apply the daily automatic synchronization time."""
        clean_value = value.replace(tzinfo=None)
        options = dict(self.entry.options)
        options[CONF_AUTO_SYNC_TIME] = clean_value.isoformat()
        self.hass.config_entries.async_update_entry(self.entry, options=options)
        self._schedule_auto_sync()
        self.async_update_listeners()

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
        now = dt_util.now()
        offset = now.utcoffset()
        offset_seconds = int(offset.total_seconds()) if offset is not None else 0
        local_epoch = int(now.timestamp()) + offset_seconds
        await self.api.async_write_u32(DATE_TIME_UUID, local_epoch)
