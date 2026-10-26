"""Constants for the Noyce Joyce Nixie integration."""

from datetime import timedelta

DOMAIN = "noyce_joyce_nixie"
NAME = "Noyce Joyce Nixie"
MANUFACTURER = "Noyce Joyce"
MODEL = "Nixie Clock"

UPDATE_INTERVAL = timedelta(minutes=5)

SERVICE_UUID = "a8ed1400-130a-4d4b-acba-5de7e77e9b47"
DATE_TIME_UUID = "a8ed1410-130a-4d4b-acba-5de7e77e9b47"
TIME_FORMAT_UUID = "a8ed1420-130a-4d4b-acba-5de7e77e9b47"
HOURGLASS_UUID = "a8ed1421-130a-4d4b-acba-5de7e77e9b47"
NIGHT_MODE_UUID = "a8ed1423-130a-4d4b-acba-5de7e77e9b47"
NIGHT_MODE_END_UUID = "a8ed1424-130a-4d4b-acba-5de7e77e9b47"  # Display ON time
NIGHT_MODE_START_UUID = "a8ed1425-130a-4d4b-acba-5de7e77e9b47"  # Display OFF time
NIXIE_DOTS_UUID = "a8ed1426-130a-4d4b-acba-5de7e77e9b47"
BOOTLOADER_UUID = "a8ed14ff-130a-4d4b-acba-5de7e77e9b47"  # Intentionally unused

DEVICE_INFO_SERVICE_UUID = "0000180a-0000-1000-8000-00805f9b34fb"
FIRMWARE_REVISION_UUID = "00002a26-0000-1000-8000-00805f9b34fb"

CONF_AUTO_SYNC_ENABLED = "auto_sync_enabled"
CONF_AUTO_SYNC_TIME = "auto_sync_time"
DEFAULT_AUTO_SYNC_ENABLED = True
DEFAULT_AUTO_SYNC_TIME = "04:05:00"

HOURGLASS_OPTIONS = {
    0: "Hvert minutt",
    1: "Hvert 10. minutt",
    2: "Hvert 30. minutt",
    3: "Hver time",
    4: "Av",
}
HOURGLASS_VALUES = {label: value for value, label in HOURGLASS_OPTIONS.items()}

TIME_FORMAT_OPTIONS = {
    0: "24 timer",
    1: "12 timer",
}
TIME_FORMAT_VALUES = {label: value for value, label in TIME_FORMAT_OPTIONS.items()}
