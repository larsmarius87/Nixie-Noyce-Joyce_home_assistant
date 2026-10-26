"""Constants for the Noyce Joyce Nixie integration."""

DOMAIN = "noyce_joyce_nixie"
MANUFACTURER = "Noyce Joyce"
MODEL = "Nixie Clock"

SERVICE_UUID = "a8ed1400-130a-4d4b-acba-5de7e77e9b47"
DATE_TIME_UUID = "a8ed1410-130a-4d4b-acba-5de7e77e9b47"
TIME_FORMAT_UUID = "a8ed1420-130a-4d4b-acba-5de7e77e9b47"
HOURGLASS_UUID = "a8ed1421-130a-4d4b-acba-5de7e77e9b47"
NIGHT_MODE_UUID = "a8ed1423-130a-4d4b-acba-5de7e77e9b47"
NIGHT_ON_UUID = "a8ed1424-130a-4d4b-acba-5de7e77e9b47"
NIGHT_OFF_UUID = "a8ed1425-130a-4d4b-acba-5de7e77e9b47"
NIXIE_DOTS_UUID = "a8ed1426-130a-4d4b-acba-5de7e77e9b47"
FIRMWARE_REV_UUID = "00002a26-0000-1000-8000-00805f9b34fb"

TIME_FORMAT_OPTIONS = {
    "24 timer": 0,
    "12 timer": 1,
}
TIME_FORMAT_FROM_RAW = {value: label for label, value in TIME_FORMAT_OPTIONS.items()}

# Confirmed from the firmware's anti-poisoning scheduler.
HOURGLASS_OPTIONS = {
    "1 minutt": 0,
    "10 minutter": 1,
    "30 minutter": 2,
    "60 minutter": 3,
    "24 timer": 4,
}
HOURGLASS_FROM_RAW = {value: label for label, value in HOURGLASS_OPTIONS.items()}

UPDATE_INTERVAL_SECONDS = 300
