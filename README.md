# Noyce Joyce Nixie – Home Assistant custom integration

First beta built by reverse engineering the official Noyce Joyce Nixie Android app (1.0.7) and its bundled firmware (1.17).

## Supported in v0.1.0

- Nixie dots: on/off
- Night mode: on/off
- Night-mode display ON time
- Night-mode display OFF time
- Time format: 24 h / 12 h
- Hourglass / anti-poisoning interval: 1 min / 10 min / 30 min / 60 min / 24 h
- Firmware version diagnostic sensor

The integration communicates locally and directly over Bluetooth LE. No cloud service is used.

## Install

1. Copy the folder `custom_components/noyce_joyce_nixie` to `/config/custom_components/noyce_joyce_nixie` in Home Assistant.
2. Restart Home Assistant.
3. Keep the Nixie clock powered on and in Bluetooth range.
4. Home Assistant should discover `Nixie Clock`. If not, go to **Settings → Devices & services → Add integration → Noyce Joyce Nixie**.

## Notes

- The clock uses an nRF52 BLE controller and the custom GATT service `A8ED1400-130A-4D4B-ACBA-5DE7E77E9B47`.
- Settings are read every 5 minutes; writes are applied immediately and followed by a refresh.
- Clock/date synchronization is intentionally not exposed in this first beta. The firmware format is known, but the official app's timezone convention should be verified against a real clock before Home Assistant is allowed to set the RTC.
