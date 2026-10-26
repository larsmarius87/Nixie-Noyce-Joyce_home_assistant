"""Button entities for Noyce Joyce Nixie."""

from homeassistant.components.button import ButtonEntity
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
    async_add_entities([SyncClockButton(entry.runtime_data)])


class SyncClockButton(NixieEntity, ButtonEntity):
    _attr_name = "Synkroniser klokke"
    _attr_icon = "mdi:clock-sync"

    def __init__(self, coordinator):
        super().__init__(coordinator, "sync_clock")

    async def async_press(self) -> None:
        try:
            await self.coordinator.async_sync_clock()
        except NixieConnectionError as err:
            raise HomeAssistantError(str(err)) from err
