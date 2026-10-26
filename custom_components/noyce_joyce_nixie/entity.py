"""Shared entity code for Noyce Joyce Nixie."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import NoyceJoyceCoordinator


class NoyceJoyceEntity(CoordinatorEntity[NoyceJoyceCoordinator]):
    """Base entity tied to one Noyce Joyce clock."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: NoyceJoyceCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device.address}_{key}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.device.address)},
            name=self.coordinator.device.name,
            manufacturer=MANUFACTURER,
            model=MODEL,
            sw_version=(
                self.coordinator.data.firmware_version if self.coordinator.data else None
            ),
        )

    async def _refresh_after_write(self) -> None:
        await self.coordinator.async_request_refresh()
