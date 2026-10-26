"""Diagnostic sensors for Noyce Joyce Nixie."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import NoyceJoyceCoordinator
from .entity import NoyceJoyceEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator: NoyceJoyceCoordinator = entry.runtime_data
    async_add_entities([FirmwareSensor(coordinator)])


class FirmwareSensor(NoyceJoyceEntity, SensorEntity):
    _attr_name = "Firmware"
    _attr_icon = "mdi:chip"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: NoyceJoyceCoordinator) -> None:
        super().__init__(coordinator, "firmware")

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.firmware_version
