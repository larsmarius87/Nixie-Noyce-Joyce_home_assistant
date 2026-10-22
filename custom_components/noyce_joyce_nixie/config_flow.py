"""Config flow for Noyce Joyce Nixie."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.const import CONF_ADDRESS

from .const import DOMAIN, NAME, SERVICE_UUID


class NixieConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Noyce Joyce Nixie."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovery_info: BluetoothServiceInfoBleak | None = None

    async def async_step_bluetooth(self, discovery_info: BluetoothServiceInfoBleak):
        """Handle Bluetooth discovery."""
        if not discovery_info.connectable:
            return self.async_abort(reason="not_connectable")

        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        self._discovery_info = discovery_info
        self.context["title_placeholders"] = {
            "name": discovery_info.name or NAME,
        }
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input=None):
        """Confirm a discovered clock."""
        assert self._discovery_info is not None
        if user_input is not None:
            return self.async_create_entry(
                title=self._discovery_info.name or NAME,
                data={CONF_ADDRESS: self._discovery_info.address},
            )

        return self.async_show_form(
            step_id="confirm",
            description_placeholders={
                "name": self._discovery_info.name or NAME,
                "address": self._discovery_info.address,
            },
        )

    async def async_step_user(self, user_input=None):
        """Handle manual setup from the Integrations UI."""
        service_uuid = SERVICE_UUID.lower()
        found: dict[str, str] = {}
        for info in bluetooth.async_discovered_service_info(
            self.hass, connectable=True
        ):
            uuids = {uuid.lower() for uuid in info.service_uuids}
            if service_uuid in uuids or (info.name or "").lower() == "nixie clock":
                found[info.address] = f"{info.name or NAME} ({info.address})"

        if user_input is not None:
            address = user_input[CONF_ADDRESS].strip()
            await self.async_set_unique_id(address)
            self._abort_if_unique_id_configured()
            title = found.get(address, f"{NAME} ({address})")
            if title.endswith(f" ({address})"):
                title = title[: -(len(address) + 3)]
            return self.async_create_entry(
                title=title or NAME,
                data={CONF_ADDRESS: address},
            )

        if found:
            schema = vol.Schema({vol.Required(CONF_ADDRESS): vol.In(found)})
        else:
            schema = vol.Schema({vol.Required(CONF_ADDRESS): str})

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            description_placeholders={"discovery": "ja" if found else "nei"},
        )
