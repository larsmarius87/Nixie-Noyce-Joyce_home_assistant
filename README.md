# Noyce Joyce Nixie – Home Assistant custom integration

Built by reverse engineering the official Noyce Joyce Nixie Android app (1.0.7) and its bundled firmware (1.17).

## Supported in v0.3.0

- Clock synchronization from Home Assistant
- Automatic daily clock sync at 04:05 local Home Assistant time
- Manual **Synchronize clock** button
- Nixie dots: on/off
- Night mode: on/off
- Night-mode display ON time
- Night-mode display OFF time
- Time format: 24 h / 12 h
- Hourglass / anti-poisoning interval: Off / 1 min / 10 min / 30 min / 60 min
- Firmware version diagnostic sensor

The integration communicates locally and directly over Bluetooth LE. No cloud service is used.

## Install

1. Copy the folder `custom_components/noyce_joyce_nixie` to `/config/custom_components/noyce_joyce_nixie` in Home Assistant.
2. Restart Home Assistant.
3. Keep the Nixie clock powered on and in Bluetooth range.
4. Home Assistant should discover `Nixie Clock`. If not, go to **Settings → Devices & services → Add integration → Noyce Joyce Nixie**.

## Hourglass Off mapping

Firmware 1.17 does not expose a true disabled state for the hourglass / anti-poisoning effect. In Home Assistant, **Off** maps to firmware value `4`, which is the least frequent mode: once per day. The clock firmware normally runs that effect around 03:00.

## Notes

- The clock uses an nRF52 BLE controller and the custom GATT service `A8ED1400-130A-4D4B-ACBA-5DE7E77E9B47`.
- Settings are read every 5 minutes; writes are applied immediately.
- Daily synchronization uses Home Assistant local time, including the current UTC offset, so DST changes are corrected automatically at the next synchronization.
