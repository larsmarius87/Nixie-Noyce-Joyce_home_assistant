# Changelog

All notable changes to the Noyce Joyce Nixie Home Assistant integration are documented here.

## 0.6.12

- Added an on-demand Home Assistant active Bluetooth scan when neither fresh advertisements nor source-specific scanner cache entries exist for the Nixie clock.
- The existing advertisement callback remains registered during the active scan so observations from all scanners/proxies are captured.
- Candidate discovery is repeated after the scan and continues to rank sources strictly by RSSI.
- Active scanning does not establish a GATT connection to the clock; normal multi-proxy connection behavior is unchanged.
- Added diagnostic source labels showing when the active-scan fallback was used.
- Existing coordinator retry timing and automatic time-sync retry behavior remain unchanged.

## 0.6.11

- Added configurable regular Bluetooth polling interval from 1 to 360 minutes.
- Added `Bluetooth-oppdateringsintervall` number entity in minutes.
- Default regular polling interval remains 5 minutes.
- Interval changes are persisted and applied immediately by rescheduling DataUpdateCoordinator polling.
- Renamed the automatic clock synchronization interval entity from `Synkintervall` to `Tidssynk-intervall` to avoid confusion with BLE polling.
- Preserved the separate 30-second retry after failed coordinator BLE reads.

## 0.6.10

- Added configurable automatic clock synchronization interval from 1 to 24 hours.
- Default interval is 24 hours, preserving previous behavior.
- Added `Synkintervall` number entity in hours.
- The configured auto-sync time acts as the initial anchor; subsequent automatic runs use the selected interval.
- Manual synchronization does not change the automatic interval cadence.
- Changing the auto-sync anchor time resets the cadence so the new time is respected.
- Existing 10-minute BLE retry after failed automatic synchronization is preserved.
- Added `hacs.json` and HACS validation workflow.
- Added hassfest validation workflow.
- Added `documentation`, `issue_tracker`, `codeowners`, and `integration_type` to `manifest.json` for HACS/public repository readiness.

## 0.6.9

- Replaced the single cached `async_ble_device_from_address()` lookup with automatic multi-proxy source selection.
- Uses Home Assistant `async_register_advertisement_callback()` to collect fresh per-scanner advertisements for the clock.
- Supplements fresh observations with `async_scanner_devices_by_address()` source-specific cache entries.
- Ranks candidates strictly by RSSI, strongest first.
- Fresh observations override cache entries from the same scanner.
- Tries up to six Bluetooth sources per connection round and falls back to the next source on connection failure.
- Uses one Bleak connection attempt per source to avoid nested/aggressive retry loops.
- Preserves the v0.6.7 coordinator-level 30-second retry if all sources fail or the clock is temporarily not seen.
- Expanded `Sist brukt Bluetooth-proxy` attributes with RSSI at connection, candidate count, fallback count, source discovery method, and ranked candidate details.

## 0.6.8

- Added `Sist brukt Bluetooth-proxy` diagnostic sensor.
- Tracks the scanner/proxy source that actually carried the latest successful BLE connection, rather than only the most recent advertiser.
- Uses the proxy/scanner source (normally its MAC address) as sensor state.
- Adds the proxy/scanner name as an attribute when Home Assistant provides it.
- Keeps the last known source visible while the clock is temporarily offline.

## 0.6.7

- Changed startup so the integration no longer blocks config-entry setup on the first BLE connection.
- Added safe placeholder coordinator data so entity platforms can load before the clock is reachable.
- Initial BLE refresh now runs in the background after the entity platforms are set up.
- Failed BLE refreshes request a 30-second retry through Home Assistant's DataUpdateCoordinator instead of leaving the config entry in setup retry.
- BLE-dependent advanced schedule programming is deferred until the first successful clock read.
- Advanced schedule status shows `Venter på klokka` while waiting for the first successful BLE read.
- This improves recovery after Home Assistant restarts when an ESPHome Bluetooth Proxy temporarily has a stale or busy connection slot.

## 0.6.6

- Added local Home Assistant brand artwork for the integration.
- Added `brand/icon.png` and `brand/icon@2x.png`.
- Added `brand/logo.png` and `brand/logo@2x.png`.
- Updated package metadata to version 0.6.6.

## 0.6.5

- Reworked the advanced scheduler to use read-back verification.
- Home Assistant now reads the clock's current night-mode settings before writing.
- Schedule values are only written when the stored clock values differ from the desired interval.
- BLE writes use GATT write responses and are followed by an immediate read-back check.
- A schedule is only marked successful when night mode, display-off time, and display-on time all match.
- Removed unconditional repeated schedule writes every five minutes.
- Five-minute retry is now only used after BLE failure or failed read-back verification.
- Added diagnostic sensors for schedule status, programmed interval, and last verified schedule time.
- Restoring `Enkel` schedule mode is also read-back verified.

## 0.6.0

- Added reading of the Nixie clock's own RTC over BLE.
- Added `Klokkens tid` diagnostic sensor.
- Added `Klokkeavvik` diagnostic sensor showing the difference between the clock RTC and Home Assistant in seconds.
- BLE read midpoint is used when calculating clock drift to reduce transaction-latency error.
- RTC reading is fail-safe so the rest of the integration continues working if a firmware variant cannot be read.

## 0.5.0

- Added advanced display scheduling.
- Added `Enkel` and `Ukedag / helg` schedule modes.
- Added separate weekday display-off and display-on times.
- Added separate weekend display-off and display-on times.
- Added optional daytime display-off period for Monday through Friday.
- Home Assistant dynamically programs the clock's single internal night-mode interval with the next relevant display window.
- Weekend selection follows the morning/display-on day, so Friday night uses the Saturday profile and Sunday night uses the Monday profile.
- Added next scheduled event sensor.
- Added last successful clock sync sensor.
- Added last successful BLE contact sensor.
- Added retry handling for failed Bluetooth operations.
- Added restoration of the original simple night-mode interval when returning to `Enkel` mode.

## 0.4.0

- Added `Auto-synk` configuration switch.
- Added adjustable `Tidspunkt for auto-synk` time entity.
- Automatic sync settings persist across Home Assistant restarts.
- Default automatic sync remains enabled at 04:05.
- Manual `Synkroniser klokke` button retained.

## 0.3.0

- Refined Hourglass / anti-poisoning presentation.
- The firmware's once-per-day mode is shown as `Av` in Home Assistant as the least intrusive option.
- Available modes: Off/once daily, every minute, every 10 minutes, every 30 minutes, and every hour.

## 0.2.0

- Added manual clock synchronization from Home Assistant.
- Added automatic daily time synchronization.
- Added timezone/DST-aware local-time conversion for RTC synchronization.
- Initial automatic sync time set to 04:05.

## 0.1.0

- Initial Home Assistant custom integration based on reverse engineering of the Noyce Joyce Android app and bundled firmware.
- Added Bluetooth discovery and connection support.
- Added firmware revision sensor.
- Added 12/24-hour format control.
- Added Nixie dots control.
- Added Night Mode control.
- Added Night Mode display-on and display-off time controls.
- Added Hourglass / anti-poisoning interval control.
- Documented the reverse-engineered BLE service and characteristic UUIDs.
