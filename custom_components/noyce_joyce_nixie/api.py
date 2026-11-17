"""BLE protocol implementation for Noyce Joyce Nixie Clock."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from bleak import BleakClient
from bleak.backends.device import BLEDevice
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


@dataclass(frozen=True, slots=True)
class NightModeSettings:
    """Night-mode values read back from the clock."""

    enabled: bool
    start_seconds: int
    end_seconds: int


@dataclass(frozen=True, slots=True)
class BluetoothCandidate:
    """One source-specific Home Assistant Bluetooth connection candidate."""

    source: str
    scanner_name: str | None
    rssi: int
    ble_device: BLEDevice
    fresh: bool


ADVERTISEMENT_COLLECTION_SECONDS = 3.0
ACTIVE_SCAN_SECONDS = 3.0
MAX_BLUETOOTH_CANDIDATES = 6


class NixieBLE:
    """Small BLE client for the Noyce Joyce Nixie Clock."""

    def __init__(self, hass: HomeAssistant, address: str, name: str) -> None:
        self.hass = hass
        self.address = address
        self.name = name
        self._operation_lock = asyncio.Lock()
        self.last_proxy_source: str | None = None
        self.last_proxy_name: str | None = None
        self.last_proxy_rssi: int | None = None
        self.last_candidate_count = 0
        self.last_connection_fallbacks = 0
        self.last_source_discovery_method: str | None = None
        self.last_candidate_details: tuple[str, ...] = ()

    async def _collect_bluetooth_candidates(self) -> list[BluetoothCandidate]:
        """Collect fresh and cached source-specific BLE devices, ranked by RSSI."""
        fresh: dict[str, BluetoothCandidate] = {}

        def _advertisement_received(service_info) -> None:
            if not service_info.connectable:
                return
            source = str(service_info.source)
            rssi = int(service_info.rssi)
            current = fresh.get(source)
            if current is None or rssi > current.rssi:
                fresh[source] = BluetoothCandidate(
                    source=source,
                    scanner_name=None,
                    rssi=rssi,
                    ble_device=service_info.device,
                    fresh=True,
                )

        cancel = bluetooth.async_register_advertisement_callback(
            self.hass, _advertisement_received, self.address
        )
        active_scan_requested = False
        try:
            # As in the Xzense multi-proxy strategy, give every scanner a short
            # window to report the device instead of accepting only HA's single
            # currently preferred BLEDevice.
            await asyncio.sleep(ADVERTISEMENT_COLLECTION_SECONDS)

            cached_devices = bluetooth.async_scanner_devices_by_address(
                self.hass, self.address, connectable=True
            )

            # If HA has neither a fresh advertisement nor a source-specific
            # cache entry, request one short bus-wide active scan before giving
            # up. This is an advertisement scan only; it does not open a GATT
            # connection to the clock. Keep the advertisement callback active
            # during the sweep so observations from every scanner are captured.
            if not fresh and not cached_devices:
                request_active_scan = getattr(
                    bluetooth, "async_request_active_scan", None
                )
                if request_active_scan is not None:
                    active_scan_requested = True
                    _LOGGER.debug(
                        "No Nixie Bluetooth source currently sees %s; "
                        "requesting %.1fs active scan",
                        self.address,
                        ACTIVE_SCAN_SECONDS,
                    )
                    await request_active_scan(self.hass, ACTIVE_SCAN_SECONDS)
                    cached_devices = bluetooth.async_scanner_devices_by_address(
                        self.hass, self.address, connectable=True
                    )
        finally:
            cancel()
        scanner_names = {
            str(item.scanner.source): str(item.scanner.name)
            for item in cached_devices
            if getattr(item.scanner, "source", None)
        }

        # Fill scanner names for fresh observations from the per-scanner cache.
        candidates: dict[str, BluetoothCandidate] = {}
        for source, candidate in fresh.items():
            candidates[source] = BluetoothCandidate(
                source=source,
                scanner_name=scanner_names.get(source),
                rssi=candidate.rssi,
                ble_device=candidate.ble_device,
                fresh=True,
            )

        # Cache is fallback only. A fresh observation from the same source always
        # wins, even if the cached RSSI happens to be higher.
        for item in cached_devices:
            source = str(item.scanner.source)
            if source in candidates:
                continue
            candidates[source] = BluetoothCandidate(
                source=source,
                scanner_name=str(item.scanner.name) if item.scanner.name else None,
                rssi=int(item.advertisement.rssi),
                ble_device=item.ble_device,
                fresh=False,
            )

        ranked = sorted(candidates.values(), key=lambda item: item.rssi, reverse=True)[
            :MAX_BLUETOOTH_CANDIDATES
        ]
        self.last_candidate_count = len(ranked)
        self.last_candidate_details = tuple(
            f"{item.source} {item.rssi} dBm ({'fersk' if item.fresh else 'cache'})"
            for item in ranked
        )
        if active_scan_requested and fresh and len(fresh) == len(ranked):
            self.last_source_discovery_method = "aktiv scan: fersk annonsering"
        elif active_scan_requested and fresh:
            self.last_source_discovery_method = "aktiv scan: fersk annonsering + cache"
        elif active_scan_requested and ranked:
            self.last_source_discovery_method = "aktiv scan: cache"
        elif active_scan_requested:
            self.last_source_discovery_method = "aktiv scan: ingen treff"
        elif fresh and len(fresh) == len(ranked):
            self.last_source_discovery_method = "fersk annonsering"
        elif fresh:
            self.last_source_discovery_method = "fersk annonsering + cache"
        elif ranked:
            self.last_source_discovery_method = "cache"
        else:
            self.last_source_discovery_method = None

        _LOGGER.debug(
            "Nixie BLE candidates for %s: %s",
            self.address,
            ", ".join(self.last_candidate_details) or "none",
        )
        return ranked

    async def _connect(self) -> BleakClient:
        candidates = await self._collect_bluetooth_candidates()
        if not candidates:
            reason = bluetooth.async_address_reachability_diagnostics(
                self.hass,
                self.address,
                bluetooth.BluetoothReachabilityIntent.CONNECTION,
            )
            raise NixieConnectionError(
                f"Ingen Bluetooth-proxy ser {self.address} akkurat nå: {reason}"
            )

        errors: list[str] = []
        for index, candidate in enumerate(candidates):
            try:
                client = await establish_connection(
                    BleakClient,
                    candidate.ble_device,
                    self.name,
                    max_attempts=1,
                )
            except (BleakError, TimeoutError) as err:
                errors.append(f"{candidate.source}: {err}")
                _LOGGER.debug(
                    "Nixie BLE connection failed via %s (%s dBm); trying next source",
                    candidate.source,
                    candidate.rssi,
                )
                continue

            self.last_proxy_source = candidate.source
            self.last_proxy_name = candidate.scanner_name
            self.last_proxy_rssi = candidate.rssi
            self.last_connection_fallbacks = index
            _LOGGER.debug(
                "Nixie BLE connected via %s (%s, %s dBm) after %s fallback(s)",
                candidate.source,
                candidate.scanner_name or "ukjent scanner",
                candidate.rssi,
                index,
            )
            return client

        self.last_connection_fallbacks = max(0, len(candidates) - 1)
        detail = "; ".join(errors)
        raise NixieConnectionError(
            f"Kunne ikke koble til {self.name} ({self.address}) via "
            f"{len(candidates)} Bluetooth-kilde(r): {detail}"
        )

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


    async def _read_night_mode_settings_from_client(
        self, client: BleakClient
    ) -> NightModeSettings:
        """Read the three values used by the firmware night-mode scheduler."""
        night_raw = await client.read_gatt_char(NIGHT_MODE_UUID)
        start_raw = await client.read_gatt_char(NIGHT_MODE_START_UUID)
        end_raw = await client.read_gatt_char(NIGHT_MODE_END_UUID)
        return NightModeSettings(
            enabled=bool(self._read_u8(night_raw)),
            start_seconds=self._read_u32_le(start_raw) % 86400,
            end_seconds=self._read_u32_le(end_raw) % 86400,
        )

    async def async_read_night_mode_settings(self) -> NightModeSettings:
        """Read the currently stored night-mode values from the clock."""
        async with self._operation_lock:
            client = await self._connect()
            try:
                return await self._read_night_mode_settings_from_client(client)
            except (BleakError, TimeoutError, ValueError) as err:
                raise NixieConnectionError(
                    f"Kunne ikke lese nattmodus fra {self.name}: {err}"
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

    async def async_program_night_mode_verified(
        self, enabled: bool, start_seconds: int, end_seconds: int
    ) -> NightModeSettings:
        """Write night-mode values and immediately read them back for verification."""
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

                # Give the firmware a very short moment to commit the values before
                # the read-back. The GATT writes already use response=True.
                await asyncio.sleep(0.1)
                return await self._read_night_mode_settings_from_client(client)
            except (BleakError, TimeoutError, ValueError) as err:
                raise NixieConnectionError(
                    f"Kunne ikke programmere og bekrefte nattmodus på {self.name}: {err}"
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
