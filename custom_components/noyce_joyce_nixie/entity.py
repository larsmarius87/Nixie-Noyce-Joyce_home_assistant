"""Base entity for Noyce Joyce Nixie."""

from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import NixieCoordinator


class NixieEntity(CoordinatorEntity[NixieCoordinator]):
    """Common Nixie entity."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: NixieCoordinator, key: str) -> None:
        super().__init__(coordinator)
        address = coordinator.api.address
        self._attr_unique_id = f"{address}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
            connections={(CONNECTION_BLUETOOTH, address)},
            manufacturer=MANUFACTURER,
            model=MODEL,
            name=coordinator.api.name,
            sw_version=coordinator.data.firmware_version,
        )
