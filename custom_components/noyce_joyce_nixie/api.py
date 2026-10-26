"""Bluetooth API for the Noyce Joyce Nixie clock."""

from __future__ import annotations

import asyncio
from contextlib import suppress
from dataclasses import dataclass
from datetime import time
import logging
import struct

from bleak import BleakClient
from bleak.exc import BleakError

from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant

from .const import (
    DATE_TIME_UUID,
    FIRMWARE_REV_UUID,
    HOURGLASS_UUID,
    NIGHT_MODE_UUID,
    NIGHT_OFF_UUID,
    NIGHT_ON_UUID,
    NIXIE_DOTS_UUID,
    TIME_FORMAT_UUID,
)

_LOGGER = logging.getLogger(__name__)


class NoyceJoyceError(Exception):
    """Base error for Noyce Joyce communication."""


class NoyceJoyceNotFoundError(NoyceJoyceError):
    """Raised when the clock is not currently reachable."""


class NoyceJoyceCommunicationError(NoyceJoyceError):
    """Raised when BLE communication fails."""


@dataclass(slots=True)
class NixieState:
    """Current configurable state read from the clock."""

    time_format: int
    hourglass: int
    night_mode: bool
    night_on: time
    night_off: time
    nixie_dots: bool
    firmware_version: str | None


def _decode_u8(value: bytearray | bytes) -> int:
    if not value:
        raise NoyceJoyceCommunicationError("Clock returned an empty 1-byte value")
    return int(value[0])


def _decode_seconds_since_midnight(value: bytearray | bytes) -> time:
    if len(value) < 4:
        raise NoyceJoyceCommunicationError(
            f"Expected 4 bytes for night-mode time, got {len(value)}"
        )
    seconds = struct.unpack_from("<I", value)[0] % 86400
    hour, remainder = divmod(seconds, 3600)
    minute, second = divmod(remainder, 60)
    return time(hour=hour, minute=minute, second=second)


def _encode_seconds_since_midnight(value: time) -> bytes:
    seconds = value.hour * 3600 + value.minute * 60 + value.second
    return struct.pack("<I", seconds)


def _encode_clock_datetime(local_now) -> bytes:
    """Encode local wall-clock time for the Nixie firmware.

    The firmware converts the received 32-bit value into calendar fields without
    having a user-configurable timezone. To represent Home Assistant local wall
    time, encode Unix time plus the current local UTC offset. This matches the
    firmware's calendar-field conversion and handles daylight-saving changes.
    """
    utc_offset = local_now.utcoffset()
    offset_seconds = int(utc_offset.total_seconds()) if utc_offset else 0
    timestamp = int(local_now.timestamp()) + offset_seconds
    if not 0 <= timestamp <= 0xFFFFFFFF:
        raise ValueError("Clock timestamp is outside the firmware's uint32 range")
    return struct.pack("<I", timestamp)


class NoyceJoyceNixie:
    """Direct BLE client for a Noyce Joyce Nixie clock."""

    def __init__(self, hass: HomeAssistant, address: str, name: str) -> None:
        self.hass = hass
        self.address = address.upper()
        self.name = name
        self._lock = asyncio.Lock()

    def _ble_device(self):
        device = bluetooth.async_ble_device_from_address(
            self.hass, self.address, connectable=True
        )
        if device is None:
            raise NoyceJoyceNotFoundError(
                f"Noyce Joyce Nixie {self.address} is not currently reachable"
            )
        return device

    async def _connect(self) -> BleakClient:
        device = self._ble_device()
        client = BleakClient(device, timeout=12.0)
        try:
            await client.connect()
        except (BleakError, TimeoutError, asyncio.TimeoutError) as err:
            raise NoyceJoyceCommunicationError(
                f"Could not connect to {self.name} ({self.address}): {err}"
            ) from err
        return client

    async def async_read_state(self) -> NixieState:
        """Read all settings in a single BLE connection."""
        async with self._lock:
            client = await self._connect()
            try:
                time_format = _decode_u8(await client.read_gatt_char(TIME_FORMAT_UUID))
                hourglass = _decode_u8(await client.read_gatt_char(HOURGLASS_UUID))
                night_mode = bool(_decode_u8(await client.read_gatt_char(NIGHT_MODE_UUID)))
                night_on = _decode_seconds_since_midnight(
                    await client.read_gatt_char(NIGHT_ON_UUID)
                )
                night_off = _decode_seconds_since_midnight(
                    await client.read_gatt_char(NIGHT_OFF_UUID)
                )
                nixie_dots = bool(
                    _decode_u8(await client.read_gatt_char(NIXIE_DOTS_UUID))
                )

                firmware_version: str | None = None
                try:
                    fw_raw = await client.read_gatt_char(FIRMWARE_REV_UUID)
                    firmware_version = bytes(fw_raw).decode("utf-8", errors="replace").strip(
                        "\x00 "
                    ) or None
                except BleakError:
                    _LOGGER.debug("Firmware revision characteristic could not be read")

                return NixieState(
                    time_format=time_format,
                    hourglass=hourglass,
                    night_mode=night_mode,
                    night_on=night_on,
                    night_off=night_off,
                    nixie_dots=nixie_dots,
                    firmware_version=firmware_version,
                )
            except (BleakError, TimeoutError, asyncio.TimeoutError) as err:
                raise NoyceJoyceCommunicationError(
                    f"Could not read settings from {self.name}: {err}"
                ) from err
            finally:
                if client.is_connected:
                    with suppress(BleakError, TimeoutError):
                        await client.disconnect()

    async def async_write_u8(self, characteristic: str, value: int) -> None:
        """Write one unsigned byte to a characteristic."""
        if not 0 <= value <= 255:
            raise ValueError("u8 value must be between 0 and 255")
        await self._async_write(characteristic, bytes((value,)))

    async def async_write_time(self, characteristic: str, value: time) -> None:
        """Write a night-mode time as little-endian seconds since midnight."""
        await self._async_write(characteristic, _encode_seconds_since_midnight(value))

    async def async_sync_clock(self) -> None:
        """Synchronize the clock RTC with Home Assistant's local time."""
        from homeassistant.util import dt as dt_util

        local_now = dt_util.now()
        await self._async_write(DATE_TIME_UUID, _encode_clock_datetime(local_now))
        _LOGGER.info("Synchronized %s to %s", self.name, local_now.isoformat())

    async def _async_write(self, characteristic: str, payload: bytes) -> None:
        """Write to the clock using a short-lived BLE connection."""
        async with self._lock:
            client = await self._connect()
            try:
                await client.write_gatt_char(characteristic, payload, response=True)
            except (BleakError, TimeoutError, asyncio.TimeoutError) as err:
                raise NoyceJoyceCommunicationError(
                    f"Could not write to {self.name}: {err}"
                ) from err
            finally:
                if client.is_connected:
                    with suppress(BleakError, TimeoutError):
                        await client.disconnect()
