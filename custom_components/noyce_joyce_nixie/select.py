"""Select entities for Noyce Joyce Nixie."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    HOURGLASS_FROM_RAW,
    HOURGLASS_OPTIONS,
    HOURGLASS_UUID,
    TIME_FORMAT_FROM_RAW,
    TIME_FORMAT_OPTIONS,
    TIME_FORMAT_UUID,
)
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
            TimeFormatSelect(coordinator),
            HourglassSelect(coordinator),
        ]
    )


class TimeFormatSelect(NoyceJoyceEntity, SelectEntity):
    _attr_name = "Tidsformat"
    _attr_icon = "mdi:clock-digital"
    _attr_options = list(TIME_FORMAT_OPTIONS)

    def __init__(self, coordinator: NoyceJoyceCoordinator) -> None:
        super().__init__(coordinator, "time_format")

    @property
    def current_option(self) -> str | None:
        return TIME_FORMAT_FROM_RAW.get(self.coordinator.data.time_format)

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.device.async_write_u8(
            TIME_FORMAT_UUID, TIME_FORMAT_OPTIONS[option]
        )
        await self._refresh_after_write()


class HourglassSelect(NoyceJoyceEntity, SelectEntity):
    _attr_name = "Hourglass-intervall"
    _attr_icon = "mdi:timer-sand"
    _attr_options = list(HOURGLASS_OPTIONS)

    def __init__(self, coordinator: NoyceJoyceCoordinator) -> None:
        super().__init__(coordinator, "hourglass")

    @property
    def current_option(self) -> str | None:
        return HOURGLASS_FROM_RAW.get(self.coordinator.data.hourglass)

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.device.async_write_u8(
            HOURGLASS_UUID, HOURGLASS_OPTIONS[option]
        )
        await self._refresh_after_write()
