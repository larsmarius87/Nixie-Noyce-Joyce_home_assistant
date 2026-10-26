# Reverse-engineered BLE protocol

Base UUID suffix: `-130A-4D4B-ACBA-5DE7E77E9B47`

| UUID | Meaning | Encoding |
|---|---|---|
| A8ED1400... | Main custom service | Service |
| A8ED1410... | Date/time | 4-byte little-endian local Unix-like time value; read + write used for RTC display/sync |
| A8ED1420... | Time format | u8: 0 = 24 h, 1 = 12 h |
| A8ED1421... | Hourglass / anti-poisoning | u8: 0=1 min, 1=10 min, 2=30 min, 3=60 min, 4=24 h (shown as Off in HA) |
| A8ED1423... | Night mode enabled | u8: 0/1 |
| A8ED1424... | Night-mode display ON time | uint32 little-endian seconds since midnight |
| A8ED1425... | Night-mode display OFF time | uint32 little-endian seconds since midnight |
| A8ED1426... | Nixie dots | u8: 0/1 |
| A8ED14FF... | DFU/bootloader-related | not used for normal control |

Firmware revision is available through the standard Device Information characteristic `00002A26-0000-1000-8000-00805F9B34FB`.

The hourglass mapping was confirmed in firmware by the scheduler conditions: every minute, minute mod 10, minute mod 30, hourly, and once daily.


## RTC drift measurement

The Home Assistant integration reads `A8ED1410...` and compares the returned local-epoch value with the expected Home Assistant local-epoch value at the midpoint of the BLE read. This compensates for most BLE transaction latency. Because the device value has one-second resolution, sub-second drift values should be treated as approximate.
