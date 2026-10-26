"""BLE protocol implementation for Noyce Joyce Nixie Clock."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from bleak import BleakClient
from bleak.exc import BleakError
from bleak_retry_connector import establish_connection
from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import (
    DATE_TIME_UUID,
    FIRMWARE_REVISION_UUID,
    HOURGLASS_UUID,
    NIGHT_MODE_END_UUID,
    NIGHT_MODE_START_UUID,
    NIGHT_MODE_UUID,
    NIXIE_DOTS_UUID,
    TIME_FORMAT_UUID,
)

_LOGGER = logging.getLogger(__name__)


class NixieConnectionError(Exception):
    """Raised when the clock cannot be reached over BLE."""


@dataclass(frozen=True, slots=True)
class NixieState:
    """State read from the clock."""

    firmware_version: str | None
    hourglass: int
    time_format: int
    nixie_dots: bool
    night_mode: bool
    night_mode_start: int
    night_mode_end: int
    clock_time: datetime | None
    clock_drift_seconds: float | None
    clock_read_at: datetime | None


class NixieBLE:
    """Small BLE client for the Noyce Joyce Nixie Clock."""

    def __init__(self, hass: HomeAssistant, address: str, name: str) -> None:
        self.hass = hass
        self.address = address
        self.name = name
        self._operation_lock = asyncio.Lock()

    async def _connect(self) -> BleakClient:
        device = bluetooth.async_ble_device_from_address(
            self.hass, self.address, connectable=True
        )
        if device is None:
            reason = bluetooth.async_address_reachability_diagnostics(
                self.hass,
                self.address,
                bluetooth.BluetoothReachabilityIntent.CONNECTION,
            )
            raise NixieConnectionError(
                f"Fant ingen Bluetooth-adapter som kan koble til {self.address}: {reason}"
            )

        try:
            return await establish_connection(
                BleakClient,
                device,
                self.name,
                max_attempts=3,
            )
        except (BleakError, TimeoutError) as err:
            raise NixieConnectionError(
                f"Kunne ikke koble til {self.name} ({self.address}): {err}"
            ) from err

    @staticmethod
    def _read_u8(value: bytearray) -> int:
        if not value:
            raise ValueError("Tom verdi fra BLE-characteristic")
        return int(value[0])

    @staticmethod
    def _read_u32_le(value: bytearray) -> int:
        if len(value) < 4:
            raise ValueError(f"For kort 32-bit BLE-verdi: {value.hex()}")
        return int.from_bytes(value[:4], "little", signed=False)

    async def async_read_state(self) -> NixieState:
        """Read all settings in one BLE connection."""
        async with self._operation_lock:
            client = await self._connect()
            try:
                firmware_raw = await client.read_gatt_char(FIRMWARE_REVISION_UUID)

                # The official app exposes the clock RTC time. Read it independently so
                # a firmware variant without Date/Time Read support does not break the
                # rest of the integration. The value uses the same local Unix-like
                # encoding that we write when synchronizing the clock.
                clock_time = None
                clock_drift_seconds = None
                clock_read_at = None
                try:
                    read_started = datetime.now(timezone.utc)
                    clock_raw = await client.read_gatt_char(DATE_TIME_UUID)
                    read_finished = datetime.now(timezone.utc)
                    clock_epoch = self._read_u32_le(clock_raw)

                    midpoint_ts = (
                        read_started.timestamp() + read_finished.timestamp()
                    ) / 2.0
                    midpoint_utc = datetime.fromtimestamp(midpoint_ts, timezone.utc)
                    midpoint_local = dt_util.as_local(midpoint_utc)
                    offset = midpoint_local.utcoffset()
                    offset_seconds = int(offset.total_seconds()) if offset else 0
                    expected_local_epoch = midpoint_ts + offset_seconds
                    clock_drift_seconds = clock_epoch - expected_local_epoch

                    # Interpret the device epoch as local wall-clock fields.
                    wall_fields = datetime.fromtimestamp(clock_epoch, timezone.utc)
                    clock_time = wall_fields.replace(tzinfo=None).replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)
                    clock_read_at = midpoint_utc
                except (BleakError, TimeoutError, ValueError) as err:
                    _LOGGER.debug(
                        "Could not read Nixie RTC time; other settings remain available: %s",
                        err,
                    )

                hourglass_raw = await client.read_gatt_char(HOURGLASS_UUID)
                time_format_raw = await client.read_gatt_char(TIME_FORMAT_UUID)
                dots_raw = await client.read_gatt_char(NIXIE_DOTS_UUID)
                night_raw = await client.read_gatt_char(NIGHT_MODE_UUID)
                start_raw = await client.read_gatt_char(NIGHT_MODE_START_UUID)
                end_raw = await client.read_gatt_char(NIGHT_MODE_END_UUID)

                firmware = bytes(firmware_raw).decode("utf-8", errors="replace").strip("\x00 ")
                hourglass = self._read_u8(hourglass_raw)
                time_format = self._read_u8(time_format_raw)

                # Firmware constrains these values. Clamp only for HA display safety.
                if hourglass not in range(5):
                    _LOGGER.warning("Unexpected hourglass value from clock: %s", hourglass)
                if time_format not in (0, 1):
                    _LOGGER.warning("Unexpected time-format value from clock: %s", time_format)

                return NixieState(
                    firmware_version=firmware or None,
                    hourglass=hourglass,
                    time_format=time_format,
                    nixie_dots=bool(self._read_u8(dots_raw)),
                    night_mode=bool(self._read_u8(night_raw)),
                    night_mode_start=self._read_u32_le(start_raw) % 86400,
                    night_mode_end=self._read_u32_le(end_raw) % 86400,
                    clock_time=clock_time,
                    clock_drift_seconds=clock_drift_seconds,
                    clock_read_at=clock_read_at,
                )
            except (BleakError, TimeoutError, ValueError) as err:
                raise NixieConnectionError(
                    f"Kunne ikke lese innstillinger fra {self.name}: {err}"
                ) from err
            finally:
                if client.is_connected:
                    try:
                        await client.disconnect()
                    except BleakError:
                        _LOGGER.debug("BLE disconnect failed", exc_info=True)


    async def async_program_night_mode(
        self, enabled: bool, start_seconds: int, end_seconds: int
    ) -> None:
        """Program night-mode enabled state and both times in one BLE connection."""
        async with self._operation_lock:
            client = await self._connect()
            try:
                await client.write_gatt_char(
                    NIGHT_MODE_UUID, bytes((int(enabled),)), response=True
                )
                await client.write_gatt_char(
                    NIGHT_MODE_START_UUID,
                    int(start_seconds % 86400).to_bytes(4, "little", signed=False),
                    response=True,
                )
                await client.write_gatt_char(
                    NIGHT_MODE_END_UUID,
                    int(end_seconds % 86400).to_bytes(4, "little", signed=False),
                    response=True,
                )
            except (BleakError, TimeoutError) as err:
                raise NixieConnectionError(
                    f"Kunne ikke programmere nattmodus på {self.name}: {err}"
                ) from err
            finally:
                if client.is_connected:
                    try:
                        await client.disconnect()
                    except BleakError:
                        _LOGGER.debug("BLE disconnect failed", exc_info=True)

    async def async_write_u8(self, characteristic: str, value: int) -> None:
        """Write one byte to a clock characteristic."""
        await self.async_write(characteristic, bytes((value & 0xFF,)))

    async def async_write_u32(self, characteristic: str, value: int) -> None:
        """Write a little-endian unsigned 32-bit value."""
        await self.async_write(
            characteristic,
            int(value & 0xFFFFFFFF).to_bytes(4, "little", signed=False),
        )

    async def async_write(self, characteristic: str, payload: bytes) -> None:
        """Write a raw payload using a fresh BLE connection."""
        async with self._operation_lock:
            client = await self._connect()
            try:
                # The clock exposes its settings as GATT Read + Write characteristics.
                await client.write_gatt_char(characteristic, payload, response=True)
            except (BleakError, TimeoutError) as err:
                raise NixieConnectionError(
                    f"Kunne ikke skrive til {self.name}: {err}"
                ) from err
            finally:
                if client.is_connected:
                    try:
                        await client.disconnect()
                    except BleakError:
                        _LOGGER.debug("BLE disconnect failed", exc_info=True)
