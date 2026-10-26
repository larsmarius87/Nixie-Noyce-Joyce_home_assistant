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
CONF_LAST_SYNC_AT = "last_sync_at"
DEFAULT_AUTO_SYNC_ENABLED = True
DEFAULT_AUTO_SYNC_TIME = "04:05:00"

CONF_SCHEDULE_MODE = "schedule_mode"
CONF_SIMPLE_NIGHT_MODE_ENABLED = "simple_night_mode_enabled"
CONF_SIMPLE_NIGHT_START_TIME = "simple_night_start_time"
CONF_SIMPLE_NIGHT_END_TIME = "simple_night_end_time"
SCHEDULE_MODE_SIMPLE = "simple"
SCHEDULE_MODE_WEEKDAY_WEEKEND = "weekday_weekend"
SCHEDULE_MODE_OPTIONS = {
    SCHEDULE_MODE_SIMPLE: "Enkel",
    SCHEDULE_MODE_WEEKDAY_WEEKEND: "Ukedag / helg",
}
SCHEDULE_MODE_VALUES = {label: value for value, label in SCHEDULE_MODE_OPTIONS.items()}

CONF_WEEKDAY_OFF_TIME = "weekday_off_time"
CONF_WEEKDAY_ON_TIME = "weekday_on_time"
CONF_WEEKEND_OFF_TIME = "weekend_off_time"
CONF_WEEKEND_ON_TIME = "weekend_on_time"
CONF_DAYTIME_ENABLED = "daytime_enabled"
CONF_DAYTIME_OFF_TIME = "daytime_off_time"
CONF_DAYTIME_ON_TIME = "daytime_on_time"

DEFAULT_DAYTIME_ENABLED = False
DEFAULT_DAYTIME_OFF_TIME = "08:30:00"
DEFAULT_DAYTIME_ON_TIME = "15:00:00"

SCHEDULE_RETRY_DELAY = timedelta(minutes=5)
SYNC_RETRY_DELAY = timedelta(minutes=10)
SCHEDULE_END_GRACE = timedelta(seconds=10)

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
