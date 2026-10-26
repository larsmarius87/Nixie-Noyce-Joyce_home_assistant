"""Time entities for Noyce Joyce Nixie."""

from datetime import time

from homeassistant.components.time import TimeEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import NixieConfigEntry
from .api import NixieConnectionError
from .entity import NixieEntity


def _seconds_to_time(seconds: int) -> time:
    seconds %= 86400
    hour, remainder = divmod(seconds, 3600)
    minute, second = divmod(remainder, 60)
    return time(hour=hour, minute=minute, second=second)


def _time_to_seconds(value: time) -> int:
    return value.hour * 3600 + value.minute * 60 + value.second


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NixieConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        [NightModeStartTime(coordinator), NightModeEndTime(coordinator)]
    )


class NightModeStartTime(NixieEntity, TimeEntity):
    _attr_name = "Nattmodus start"
    _attr_icon = "mdi:weather-sunset-down"

    def __init__(self, coordinator):
        super().__init__(coordinator, "night_mode_start")

    @property
    def native_value(self) -> time:
        return _seconds_to_time(self.coordinator.data.night_mode_start)

    async def async_set_value(self, value: time) -> None:
        try:
            await self.coordinator.async_set_night_start(_time_to_seconds(value))
        except NixieConnectionError as err:
            raise HomeAssistantError(str(err)) from err


class NightModeEndTime(NixieEntity, TimeEntity):
    _attr_name = "Nattmodus slutt"
    _attr_icon = "mdi:weather-sunset-up"

    def __init__(self, coordinator):
        super().__init__(coordinator, "night_mode_end")

    @property
    def native_value(self) -> time:
        return _seconds_to_time(self.coordinator.data.night_mode_end)

    async def async_set_value(self, value: time) -> None:
        try:
            await self.coordinator.async_set_night_end(_time_to_seconds(value))
        except NixieConnectionError as err:
            raise HomeAssistantError(str(err)) from err
