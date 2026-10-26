"""Time entities for Noyce Joyce Nixie night mode."""

from __future__ import annotations

from datetime import time

from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import NIGHT_OFF_UUID, NIGHT_ON_UUID
from .coordinator import NoyceJoyceCoordinator
from .entity import NoyceJoyceEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator: NoyceJoyceCoordinator = entry.runtime_data
    async_add_entities(
        [
            NightOnTime(coordinator),
            NightOffTime(coordinator),
        ]
    )


class NightOnTime(NoyceJoyceEntity, TimeEntity):
    _attr_name = "Nattmodus – display på"
    _attr_icon = "mdi:weather-sunset-up"

    def __init__(self, coordinator: NoyceJoyceCoordinator) -> None:
        super().__init__(coordinator, "night_on")

    @property
    def native_value(self) -> time:
        return self.coordinator.data.night_on

    async def async_set_value(self, value: time) -> None:
        await self.coordinator.device.async_write_time(NIGHT_ON_UUID, value)
        await self._refresh_after_write()


class NightOffTime(NoyceJoyceEntity, TimeEntity):
    _attr_name = "Nattmodus – display av"
    _attr_icon = "mdi:weather-sunset-down"

    def __init__(self, coordinator: NoyceJoyceCoordinator) -> None:
        super().__init__(coordinator, "night_off")

    @property
    def native_value(self) -> time:
        return self.coordinator.data.night_off

    async def async_set_value(self, value: time) -> None:
        await self.coordinator.device.async_write_time(NIGHT_OFF_UUID, value)
        await self._refresh_after_write()
