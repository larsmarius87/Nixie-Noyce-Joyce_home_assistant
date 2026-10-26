"""Button entities for Noyce Joyce Nixie."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import NoyceJoyceError
from .coordinator import NoyceJoyceCoordinator
from .entity import NoyceJoyceEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Noyce Joyce button entities."""
    coordinator: NoyceJoyceCoordinator = entry.runtime_data
    async_add_entities([SyncClockButton(coordinator)])


class SyncClockButton(NoyceJoyceEntity, ButtonEntity):
    """Synchronize the Nixie clock with Home Assistant time."""

    _attr_name = "Synkroniser klokke nå"
    _attr_icon = "mdi:clock-sync"

    def __init__(self, coordinator: NoyceJoyceCoordinator) -> None:
        super().__init__(coordinator, "sync_clock")

    async def async_press(self) -> None:
        """Synchronize clock time immediately."""
        try:
            await self.coordinator.async_sync_clock()
        except NoyceJoyceError as err:
            raise HomeAssistantError(str(err)) from err
