"""Number entities for Noyce Joyce Nixie."""

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import NixieConfigEntry
from .const import (
    MAX_AUTO_SYNC_INTERVAL_HOURS,
    MAX_BLUETOOTH_UPDATE_INTERVAL_MINUTES,
    MIN_AUTO_SYNC_INTERVAL_HOURS,
    MIN_BLUETOOTH_UPDATE_INTERVAL_MINUTES,
)
from .entity import NixieEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NixieConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Noyce Joyce number entities."""
    async_add_entities(
        [
            AutoSyncIntervalNumber(entry.runtime_data),
            BluetoothUpdateIntervalNumber(entry.runtime_data),
        ]
    )


class AutoSyncIntervalNumber(NixieEntity, NumberEntity):
    """Adjust the automatic clock synchronization interval."""

    _attr_name = "Tidssynk-intervall"
    _attr_icon = "mdi:timer-sync-outline"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = MIN_AUTO_SYNC_INTERVAL_HOURS
    _attr_native_max_value = MAX_AUTO_SYNC_INTERVAL_HOURS
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "h"
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator):
        super().__init__(coordinator, "auto_sync_interval_hours")

    @property
    def available(self) -> bool:
        return True

    @property
    def native_value(self) -> float:
        return float(self.coordinator.auto_sync_interval_hours)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_auto_sync_interval_hours(round(value))
        self.async_write_ha_state()


class BluetoothUpdateIntervalNumber(NixieEntity, NumberEntity):
    """Adjust how often Home Assistant connects to the clock over Bluetooth."""

    _attr_name = "Bluetooth-oppdateringsintervall"
    _attr_icon = "mdi:bluetooth-connect"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = MIN_BLUETOOTH_UPDATE_INTERVAL_MINUTES
    _attr_native_max_value = MAX_BLUETOOTH_UPDATE_INTERVAL_MINUTES
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "min"
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator):
        super().__init__(coordinator, "bluetooth_update_interval_minutes")

    @property
    def available(self) -> bool:
        return True

    @property
    def native_value(self) -> float:
        return float(self.coordinator.bluetooth_update_interval_minutes)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_bluetooth_update_interval_minutes(round(value))
        self.async_write_ha_state()
