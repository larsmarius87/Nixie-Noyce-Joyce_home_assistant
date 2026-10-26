"""Switch entities for Noyce Joyce Nixie."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import NIGHT_MODE_UUID, NIXIE_DOTS_UUID
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
            NixieDotsSwitch(coordinator),
            NightModeSwitch(coordinator),
        ]
    )


class NixieDotsSwitch(NoyceJoyceEntity, SwitchEntity):
    _attr_name = "Nixie-prikker"
    _attr_icon = "mdi:dots-horizontal"

    def __init__(self, coordinator: NoyceJoyceCoordinator) -> None:
        super().__init__(coordinator, "nixie_dots")

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.nixie_dots

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.device.async_write_u8(NIXIE_DOTS_UUID, 1)
        await self._refresh_after_write()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.device.async_write_u8(NIXIE_DOTS_UUID, 0)
        await self._refresh_after_write()


class NightModeSwitch(NoyceJoyceEntity, SwitchEntity):
    _attr_name = "Nattmodus"
    _attr_icon = "mdi:weather-night"

    def __init__(self, coordinator: NoyceJoyceCoordinator) -> None:
        super().__init__(coordinator, "night_mode")

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.night_mode

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.device.async_write_u8(NIGHT_MODE_UUID, 1)
        await self._refresh_after_write()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.device.async_write_u8(NIGHT_MODE_UUID, 0)
        await self._refresh_after_write()
