"""Select entities for Noyce Joyce Nixie."""

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import NixieConfigEntry
from .api import NixieConnectionError
from .const import (
    HOURGLASS_OPTIONS,
    HOURGLASS_VALUES,
    SCHEDULE_MODE_OPTIONS,
    SCHEDULE_MODE_VALUES,
    TIME_FORMAT_OPTIONS,
    TIME_FORMAT_VALUES,
)
from .entity import NixieEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NixieConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        [HourglassSelect(coordinator), TimeFormatSelect(coordinator), ScheduleModeSelect(coordinator)]
    )


class HourglassSelect(NixieEntity, SelectEntity):
    _attr_name = "Timeglasseffekt"
    _attr_icon = "mdi:timer-sand"
    _attr_options = list(HOURGLASS_OPTIONS.values())

    def __init__(self, coordinator):
        super().__init__(coordinator, "hourglass")

    @property
    def current_option(self) -> str | None:
        return HOURGLASS_OPTIONS.get(self.coordinator.data.hourglass)

    async def async_select_option(self, option: str) -> None:
        try:
            await self.coordinator.async_set_hourglass(HOURGLASS_VALUES[option])
        except (KeyError, NixieConnectionError) as err:
            raise HomeAssistantError(str(err)) from err


class TimeFormatSelect(NixieEntity, SelectEntity):
    _attr_name = "Timeformat"
    _attr_icon = "mdi:clock-digital"
    _attr_options = list(TIME_FORMAT_OPTIONS.values())

    def __init__(self, coordinator):
        super().__init__(coordinator, "time_format")

    @property
    def current_option(self) -> str | None:
        return TIME_FORMAT_OPTIONS.get(self.coordinator.data.time_format)

    async def async_select_option(self, option: str) -> None:
        try:
            await self.coordinator.async_set_time_format(TIME_FORMAT_VALUES[option])
        except (KeyError, NixieConnectionError) as err:
            raise HomeAssistantError(str(err)) from err


class ScheduleModeSelect(NixieEntity, SelectEntity):
    _attr_name = "Tidsplanmodus"
    _attr_icon = "mdi:calendar-clock"
    _attr_options = list(SCHEDULE_MODE_OPTIONS.values())
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator):
        super().__init__(coordinator, "schedule_mode")

    @property
    def available(self) -> bool:
        return True

    @property
    def current_option(self) -> str:
        return SCHEDULE_MODE_OPTIONS[self.coordinator.schedule_mode]

    async def async_select_option(self, option: str) -> None:
        try:
            await self.coordinator.async_set_schedule_mode(SCHEDULE_MODE_VALUES[option])
        except (KeyError, ValueError, NixieConnectionError) as err:
            raise HomeAssistantError(str(err)) from err
