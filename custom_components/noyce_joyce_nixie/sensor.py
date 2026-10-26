"""Sensor entities for Noyce Joyce Nixie."""

from datetime import datetime, timedelta

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.helpers.entity import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from . import NixieConfigEntry
from .entity import NixieEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NixieConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        [
            FirmwareSensor(coordinator),
            ClockTimeSensor(coordinator),
            ClockDriftSensor(coordinator),
            NextScheduleEventSensor(coordinator),
            LastSyncSensor(coordinator),
            LastContactSensor(coordinator),
        ]
    )


class FirmwareSensor(NixieEntity, SensorEntity):
    _attr_name = "Firmware"
    _attr_icon = "mdi:chip"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator):
        super().__init__(coordinator, "firmware")

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.firmware_version


class ClockTimeSensor(NixieEntity, SensorEntity):
    _attr_name = "Klokkens tid"
    _attr_icon = "mdi:clock-digital"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator):
        super().__init__(coordinator, "clock_time")

    @property
    def native_value(self) -> datetime | None:
        return self.coordinator.data.clock_time

    @property
    def extra_state_attributes(self):
        read_at = self.coordinator.data.clock_read_at
        return {"avlest": read_at.isoformat()} if read_at is not None else {}


class ClockDriftSensor(NixieEntity, SensorEntity):
    _attr_name = "Klokkeavvik"
    _attr_icon = "mdi:timer-sync-outline"
    _attr_native_unit_of_measurement = "s"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator):
        super().__init__(coordinator, "clock_drift")

    @property
    def native_value(self) -> float | None:
        drift = self.coordinator.data.clock_drift_seconds
        return round(drift, 1) if drift is not None else None

    @property
    def extra_state_attributes(self):
        drift = self.coordinator.data.clock_drift_seconds
        read_at = self.coordinator.data.clock_read_at
        attrs = {
            "forklaring": "Positiv verdi betyr at Nixie-klokka går foran Home Assistant"
        }
        if read_at is not None:
            attrs["avlest"] = read_at.isoformat()
        if drift is not None:
            attrs["retning"] = "foran" if drift > 0 else "bak" if drift < 0 else "lik"
        return attrs


class NextScheduleEventSensor(NixieEntity, SensorEntity):
    _attr_name = "Neste planlagte hendelse"
    _attr_icon = "mdi:calendar-arrow-right"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator):
        super().__init__(coordinator, "next_schedule_event")

    @property
    def available(self) -> bool:
        return True

    @property
    def native_value(self) -> str | None:
        event = self.coordinator.next_schedule_event()
        if event is None:
            return None
        when, action = event
        now = dt_util.now()
        if when.date() == now.date():
            day = "i dag"
        elif when.date() == (now + timedelta(days=1)).date():
            day = "i morgen"
        else:
            day = when.strftime("%d.%m")
        return f"{action} {day} {when:%H:%M}"

    @property
    def extra_state_attributes(self):
        event = self.coordinator.next_schedule_event()
        if event is None:
            return {}
        when, action = event
        return {"handling": action, "tidspunkt": when.isoformat()}


class LastSyncSensor(NixieEntity, SensorEntity):
    _attr_name = "Sist synkronisert"
    _attr_icon = "mdi:clock-check-outline"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator):
        super().__init__(coordinator, "last_sync")

    @property
    def available(self) -> bool:
        return True

    @property
    def native_value(self) -> datetime | None:
        return self.coordinator.last_sync_at


class LastContactSensor(NixieEntity, SensorEntity):
    _attr_name = "Sist kontakt"
    _attr_icon = "mdi:bluetooth-connect"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator):
        super().__init__(coordinator, "last_contact")

    @property
    def available(self) -> bool:
        return True

    @property
    def native_value(self) -> datetime | None:
        return self.coordinator.last_contact
