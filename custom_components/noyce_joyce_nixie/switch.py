"""Switch entities for Noyce Joyce Nixie."""

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import NixieConfigEntry
from .api import NixieConnectionError
from .entity import NixieEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NixieConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        [NixieDotsSwitch(coordinator), NightModeSwitch(coordinator)]
    )


class NixieDotsSwitch(NixieEntity, SwitchEntity):
    _attr_name = "Nixie-prikker"
    _attr_icon = "mdi:dots-horizontal"

    def __init__(self, coordinator):
        super().__init__(coordinator, "nixie_dots")

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.nixie_dots

    async def async_turn_on(self, **kwargs) -> None:
        try:
            await self.coordinator.async_set_nixie_dots(True)
        except NixieConnectionError as err:
            raise HomeAssistantError(str(err)) from err

    async def async_turn_off(self, **kwargs) -> None:
        try:
            await self.coordinator.async_set_nixie_dots(False)
        except NixieConnectionError as err:
            raise HomeAssistantError(str(err)) from err


class NightModeSwitch(NixieEntity, SwitchEntity):
    _attr_name = "Nattmodus"
    _attr_icon = "mdi:weather-night"

    def __init__(self, coordinator):
        super().__init__(coordinator, "night_mode")

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.night_mode

    async def async_turn_on(self, **kwargs) -> None:
        try:
            await self.coordinator.async_set_night_mode(True)
        except NixieConnectionError as err:
            raise HomeAssistantError(str(err)) from err

    async def async_turn_off(self, **kwargs) -> None:
        try:
            await self.coordinator.async_set_night_mode(False)
        except NixieConnectionError as err:
            raise HomeAssistantError(str(err)) from err
