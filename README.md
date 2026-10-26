# Noyce Joyce Nixie – Home Assistant custom integration

Reverse engineered from the official Noyce Joyce Nixie Android app (1.0.7) and its bundled firmware (1.17).

## Supported in v0.2.0

- **Clock synchronization from Home Assistant**
  - `Synkroniser klokke nå` button for manual synchronization
  - automatic synchronization every day at **04:05 Home Assistant local time**
  - current Home Assistant UTC offset is applied, so DST/summer-time changes are corrected automatically
- Nixie dots: on/off
- Night mode: on/off
- Night-mode display ON time
- Night-mode display OFF time
- Time format: 24 h / 12 h
- Hourglass / anti-poisoning interval: 1 min / 10 min / 30 min / 60 min / 24 h
- Firmware version diagnostic sensor

The integration communicates locally and directly over Bluetooth LE. No cloud service is used.

## Install / upgrade

1. Copy the folder `custom_components/noyce_joyce_nixie` to `/config/custom_components/noyce_joyce_nixie` in Home Assistant, replacing the previous version if present.
2. Restart Home Assistant.
3. Keep the Nixie clock powered on and in Bluetooth range.
4. Home Assistant should discover `Nixie Clock`. If it is already configured, the existing device remains configured after the upgrade.

## Time synchronization

Firmware characteristic `A8ED1410-130A-4D4B-ACBA-5DE7E77E9B47` accepts a 32-bit little-endian epoch-style time value. The firmware has no user-selectable timezone and converts that value into RTC calendar fields. To produce local wall-clock time with the firmware's timezone-less RTC conversion, Home Assistant sends:

`Unix timestamp + current Home Assistant UTC offset`

For example, when Home Assistant is in UTC+02:00, the offset is added before writing the value. This also means the next daily synchronization corrects the Nixie clock after a daylight-saving-time transition.

After installing v0.2.0, use **Synkroniser klokke nå** once and verify that the displayed time matches Home Assistant. Automatic synchronization then runs daily at 04:05.

## Notes

- The clock uses an nRF52 BLE controller and the custom GATT service `A8ED1400-130A-4D4B-ACBA-5DE7E77E9B47`.
- Settings are read every 5 minutes; writes are applied immediately and followed by a refresh where relevant.
- If the clock is unreachable at 04:05, that day's automatic sync is skipped and retried at the next scheduled run. Manual sync can be used at any time.
