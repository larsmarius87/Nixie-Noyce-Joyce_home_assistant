"""Time entities for Noyce Joyce Nixie."""

from datetime import time

from homeassistant.components.time import TimeEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory
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
        [
            NightModeStartTime(coordinator),
            NightModeEndTime(coordinator),
            AutoSyncTime(coordinator),
            WeekdayOffTime(coordinator),
            WeekdayOnTime(coordinator),
            WeekendOffTime(coordinator),
            WeekendOnTime(coordinator),
            DaytimeOffTime(coordinator),
            DaytimeOnTime(coordinator),
        ]
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


class ConfigTimeEntity(NixieEntity, TimeEntity):
    _attr_entity_category = EntityCategory.CONFIG

    @property
    def available(self) -> bool:
        return True


class AutoSyncTime(ConfigTimeEntity):
    _attr_name = "Tidspunkt for auto-synk"
    _attr_icon = "mdi:clock-edit-outline"

    def __init__(self, coordinator):
        super().__init__(coordinator, "auto_sync_time")

    @property
    def native_value(self) -> time:
        return self.coordinator.auto_sync_time

    async def async_set_value(self, value: time) -> None:
        await self.coordinator.async_set_auto_sync_time(value)
        self.async_write_ha_state()


class WeekdayOffTime(ConfigTimeEntity):
    _attr_name = "Ukedag – display av"
    _attr_icon = "mdi:calendar-week-begin"

    def __init__(self, coordinator):
        super().__init__(coordinator, "weekday_off_time")

    @property
    def native_value(self) -> time:
        return self.coordinator.weekday_off_time

    async def async_set_value(self, value: time) -> None:
        await self.coordinator.async_set_weekday_off_time(value)


class WeekdayOnTime(ConfigTimeEntity):
    _attr_name = "Ukedag – display på"
    _attr_icon = "mdi:calendar-week"

    def __init__(self, coordinator):
        super().__init__(coordinator, "weekday_on_time")

    @property
    def native_value(self) -> time:
        return self.coordinator.weekday_on_time

    async def async_set_value(self, value: time) -> None:
        await self.coordinator.async_set_weekday_on_time(value)


class WeekendOffTime(ConfigTimeEntity):
    _attr_name = "Helg – display av"
    _attr_icon = "mdi:calendar-weekend-outline"

    def __init__(self, coordinator):
        super().__init__(coordinator, "weekend_off_time")

    @property
    def native_value(self) -> time:
        return self.coordinator.weekend_off_time

    async def async_set_value(self, value: time) -> None:
        await self.coordinator.async_set_weekend_off_time(value)


class WeekendOnTime(ConfigTimeEntity):
    _attr_name = "Helg – display på"
    _attr_icon = "mdi:calendar-weekend"

    def __init__(self, coordinator):
        super().__init__(coordinator, "weekend_on_time")

    @property
    def native_value(self) -> time:
        return self.coordinator.weekend_on_time

    async def async_set_value(self, value: time) -> None:
        await self.coordinator.async_set_weekend_on_time(value)


class DaytimeOffTime(ConfigTimeEntity):
    _attr_name = "Dagtid – display av"
    _attr_icon = "mdi:weather-sunny-off"

    def __init__(self, coordinator):
        super().__init__(coordinator, "daytime_off_time")

    @property
    def native_value(self) -> time:
        return self.coordinator.daytime_off_time

    async def async_set_value(self, value: time) -> None:
        await self.coordinator.async_set_daytime_off_time(value)


class DaytimeOnTime(ConfigTimeEntity):
    _attr_name = "Dagtid – display på"
    _attr_icon = "mdi:weather-sunny"

    def __init__(self, coordinator):
        super().__init__(coordinator, "daytime_on_time")

    @property
    def native_value(self) -> time:
        return self.coordinator.daytime_on_time

    async def async_set_value(self, value: time) -> None:
        await self.coordinator.async_set_daytime_on_time(value)
