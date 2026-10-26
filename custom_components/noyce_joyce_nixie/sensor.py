"""Sensor entities for Noyce Joyce Nixie."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import NixieConfigEntry
from .entity import NixieEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NixieConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([FirmwareSensor(entry.runtime_data)])


class FirmwareSensor(NixieEntity, SensorEntity):
    _attr_name = "Firmware"
    _attr_icon = "mdi:chip"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator):
        super().__init__(coordinator, "firmware")

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.firmware_version
