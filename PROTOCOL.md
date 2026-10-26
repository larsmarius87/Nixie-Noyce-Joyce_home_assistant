# Reverse-engineered BLE protocol

Base UUID suffix: `-130A-4D4B-ACBA-5DE7E77E9B47`

| UUID | Meaning | Encoding |
|---|---|---|
| A8ED1400... | Main custom service | Service |
| A8ED1410... | Date/time | uint32 little-endian local-wall-clock epoch value |
| A8ED1420... | Time format | u8: 0 = 24 h, 1 = 12 h |
| A8ED1421... | Hourglass / anti-poisoning | u8: 0=1 min, 1=10 min, 2=30 min, 3=60 min, 4=24 h |
| A8ED1423... | Night mode enabled | u8: 0/1 |
| A8ED1424... | Night-mode display ON time | uint32 little-endian seconds since midnight |
| A8ED1425... | Night-mode display OFF time | uint32 little-endian seconds since midnight |
| A8ED1426... | Nixie dots | u8: 0/1 |
| A8ED14FF... | DFU/bootloader-related | not used for normal control |

Firmware revision is available through the standard Device Information characteristic `00002A26-0000-1000-8000-00805F9B34FB`.

## Date/time characteristic

Firmware reverse engineering confirms that a 4-byte value written to `A8ED1410...` is converted to a C `struct tm`, after which the firmware writes second, minute, hour, day, month and year into its RTC. Since the device has no timezone configuration, the host must supply a value representing local wall time. Home Assistant therefore encodes synchronization as:

`uint32_le(unix_timestamp + current_utc_offset_seconds)`

This makes the displayed clock follow the Home Assistant timezone and lets the daily sync correct DST transitions.

The hourglass mapping was confirmed in firmware by the scheduler conditions: every minute, minute mod 10, minute mod 30, hourly, and once daily.
