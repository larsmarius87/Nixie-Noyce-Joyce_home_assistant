"""Config flow for Noyce Joyce Nixie."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS

from .const import DOMAIN, SERVICE_UUID


def _looks_like_nixie(info: BluetoothServiceInfoBleak) -> bool:
    service_uuids = {uuid.lower() for uuid in info.service_uuids}
    name = (info.name or "").lower()
    return SERVICE_UUID in service_uuids or "nixie clock" in name


class NoyceJoyceNixieConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle Noyce Joyce Nixie configuration."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovery_info: BluetoothServiceInfoBleak | None = None
        self._discovered_devices: dict[str, BluetoothServiceInfoBleak] = {}

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle Bluetooth discovery."""
        if not _looks_like_nixie(discovery_info):
            return self.async_abort(reason="not_supported")

        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        self._discovery_info = discovery_info
        self.context["title_placeholders"] = {
            "name": discovery_info.name or "Noyce Joyce Nixie"
        }
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm an automatically discovered clock."""
        assert self._discovery_info is not None
        if user_input is not None:
            return self.async_create_entry(
                title=self._discovery_info.name or "Noyce Joyce Nixie",
                data={CONF_ADDRESS: self._discovery_info.address},
            )
        self._set_confirm_only()
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders={
                "name": self._discovery_info.name or "Noyce Joyce Nixie"
            },
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Allow manual selection from clocks seen by Home Assistant."""
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            info = self._discovered_devices[address]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=info.name or "Noyce Joyce Nixie",
                data={CONF_ADDRESS: address},
            )

        current_ids = self._async_current_ids(include_ignore=False)
        for info in async_discovered_service_info(self.hass):
            if (
                info.address in current_ids
                or info.address in self._discovered_devices
                or not _looks_like_nixie(info)
            ):
                continue
            self._discovered_devices[info.address] = info

        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        choices = {
            address: f"{info.name or 'Noyce Joyce Nixie'} ({address})"
            for address, info in self._discovered_devices.items()
        }
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_ADDRESS): vol.In(choices)}),
        )
