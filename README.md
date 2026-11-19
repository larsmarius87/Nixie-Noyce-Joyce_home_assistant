# Noyce Joyce Nixie – Home Assistant v0.6.14

Local Bluetooth integration for the Noyce Joyce Nixie Clock.

## Features

- Manual clock synchronization
- Automatic clock synchronization with configurable time and interval from 1–24 hours
- Automatic 10-minute retry if clock synchronization fails because of Bluetooth
- 12/24-hour time format
- Nixie dots control
- Night mode
- Native night-mode display on/off times
- Hourglass / anti-poisoning effect
- Advanced weekday/weekend scheduling
- Optional weekday daytime display-off period
- Automatic programming of the next relevant display-off/display-on window into the clock's single internal night-mode interval
- Read-back verification after schedule writes
- Schedule values are only written when the values stored in the clock differ from the desired schedule
- Five-minute schedule retry only after Bluetooth failure or failed read-back verification
- Diagnostic sensors for schedule status, programmed interval, and last verified schedule
- Sensor for the next scheduled event
- Sensor for the last successful clock synchronization
- Sensor for the last successful Bluetooth contact
- Diagnostic sensor for the last Bluetooth proxy/scanner used, including MAC address and scanner name when available
- Robust Bluetooth startup: the integration does not block Home Assistant if the clock cannot be reached during startup
- Automatic multi-proxy selection: fresh and cached Bluetooth sources are ranked by RSSI and the next source is tried if a connection fails
- Active Bluetooth scan fallback when no proxy currently sees an advertisement from the clock
- Automatic duplicate-discovery suppression when the same clock is observed with a changing Bluetooth address
- Configurable regular Bluetooth polling interval from 1–360 minutes, default 5 minutes

## Schedule modes

**Simple** is the default mode and lets the clock use its normal built-in night-mode interval.

**Weekday / weekend** lets Home Assistant program the next relevant interval into the clock. The weekend profile is selected according to the morning/display-on day. This means Friday night uses the weekend profile for Saturday morning, while Sunday night uses the weekday profile for Monday morning.

The optional daytime display-off period applies Monday through Friday. Because the clock firmware can store only one night-mode interval at a time, Home Assistant automatically programs the next interval after the current one has finished. The clock itself executes the display on/off event locally once the interval has been programmed.

## Install from Marketplace

The repository is prepared for Marketplace installation. If it is not yet available through normal Marketplace search, it can be added as a custom repository:

1. Open **Marketplace → Integrations**.
2. Open the menu and choose **Custom repositories**.
3. Add `https://github.com/larsmarius87/Nixie-Noyce-Joyce_home_assistant`.
4. Select category **Integration**.
5. Install **Noyce Joyce Nixie** and restart Home Assistant.

For inclusion as a standard searchable Marketplace repository, the project also requires a published GitHub Release and submission to the Marketplace default repository list.

## Upgrade

When installed through Marketplace, use the normal Marketplace update flow.

For a manual installation, replace `custom_components/noyce_joyce_nixie` with the new version and restart Home Assistant.

Existing configuration is retained when upgrading. The advanced scheduler defaults to **Simple** mode unless it has already been configured.

## Duplicate Bluetooth discovery protection (v0.6.14)

From v0.6.14, the integration uses Home Assistant's native discovery handling instead of the custom duplicate guard introduced in v0.6.13.

- Automatic Bluetooth discovery uses one temporary shared discovery identity inside Home Assistant.
- If a Nixie config entry already exists, new automatic discovery proposals are aborted immediately, even if the clock is advertised with a different Bluetooth address.
- If no Nixie is configured, only one automatic discovery flow may be active at a time.
- The actual Bluetooth address becomes the config entry unique ID only when the first discovered clock is confirmed.
- The Bluetooth address of an existing config entry is never silently replaced.
- Manual setup remains available for users who intentionally have more than one physical Nixie clock.
- After upgrading from v0.6.13, a full Home Assistant restart is recommended to clear discovery flows that were already held in memory before the update.

## Active Bluetooth scan fallback (v0.6.12)

When no Home Assistant scanner/proxy has either a fresh advertisement or a source-specific cache entry for the clock, the integration performs one additional discovery attempt before giving up:

1. The normal 3-second advertisement collection runs first.
2. If both fresh observations and scanner cache are empty, the integration asks Home Assistant for a short active Bluetooth scan.
3. The advertisement callback remains registered during the scan so observations from all scanners can become candidates.
4. The candidate list is rebuilt and remains ranked by RSSI.
5. If the clock still does not advertise, the normal connection error and retry handling takes over.

The active scan is **not a GATT connection to the clock**. It is only an advertisement discovery fallback and therefore does not add another connect/disconnect cycle.

The Bluetooth source diagnostic reports `active scan: ...` when this fallback was used.

## Bluetooth polling interval (v0.6.11)

**Bluetooth update interval** controls how often Home Assistant performs the regular Bluetooth connection used to read the clock state and RTC.

- Range: **1–360 minutes**
- Step: **1 minute**
- Default: **5 minutes**
- The value is stored in the config entry and survives restarts.
- Changes take effect immediately by rescheduling the coordinator.
- The separate 30-second retry after a failed coordinator Bluetooth read remains unchanged.
- Clock synchronization uses its own separate **Time sync interval** setting.

## Adjustable time synchronization interval (v0.6.10)

- **Auto sync** enables or disables automatic clock synchronization.
- **Auto sync time** is used as the initial anchor before the first successful automatic synchronization.
- **Time sync interval** can be configured from **1 to 24 hours** in whole hours. Default: **24 hours**.
- After a successful automatic synchronization, the next run follows the selected interval.
- Manual synchronization does not shift the automatic schedule.
- If automatic synchronization fails because of Bluetooth, the existing retry remains **10 minutes**.
- Changing the auto-sync anchor time resets the interval anchor so the new time is used.

## Multi-proxy Bluetooth selection (v0.6.9)

From v0.6.9, the integration uses automatic source selection across Home Assistant Bluetooth scanners/proxies:

1. Fresh advertisements for the clock MAC address are collected from all scanners during a short collection window.
2. Home Assistant's source-specific scanner cache is added when a scanner did not advertise during that window.
3. Candidates are ranked strictly by RSSI, strongest first.
4. A fresh observation from a source overrides cached information from the same source.
5. Up to six Bluetooth sources are tried, with one connection attempt per source.
6. If the strongest source fails, the next candidate is tried automatically.
7. The coordinator-level 30-second retry is used if no candidate succeeds.

No proxy is hard-coded or pinned.

The **Last used Bluetooth proxy** diagnostic exposes the source used for the most recent successful Bluetooth connection, with attributes for scanner name, RSSI, candidate count, fallback count, discovery method, and the ranked candidate list.

## Robust Bluetooth startup (v0.6.7)

The first Bluetooth connection is no longer part of the blocking config-entry setup.

This is useful with ESPHome Bluetooth Proxy, where a scanner can occasionally have a stale or busy connection slot after a Home Assistant restart.

Behavior:

1. The integration finishes loading without requiring the clock to be reachable during startup.
2. Entities that depend on clock data remain unavailable until the first successful Bluetooth read.
3. The first read starts in the background.
4. If the connection fails, the integration remains loaded and the coordinator retries after **30 seconds**.
5. When the clock becomes available, the entities recover automatically.
6. Advanced schedule programming waits until at least one valid clock read has completed, avoiding competing Bluetooth connections during startup.

From v0.6.11, normal polling is configurable with **Bluetooth update interval** from 1 to 360 minutes.

## RTC and drift measurement (v0.6.0)

The integration reads the clock's RTC from the Date/Time characteristic during regular coordinator refreshes.

Two diagnostic sensors are exposed:

- **Clock time** – the wall-clock time returned by the Nixie clock at the last read.
- **Clock drift** – the difference in seconds between the Nixie RTC and Home Assistant at the Bluetooth read midpoint. Positive values mean the Nixie clock is ahead.

The read is fail-safe: if a firmware variant does not allow the Date/Time characteristic to be read, the rest of the integration continues to work.

## Verified scheduler (v0.6.5)

In advanced **Weekday / weekend** mode, schedule programming is verified with read-back:

1. Home Assistant first reads the current Night mode, Display OFF, and Display ON values from the clock.
2. If the values already match the desired interval, nothing is written.
3. If they differ, the three values are written using GATT write responses.
4. The integration immediately reads the values back from the clock.
5. The schedule is only marked successful when enabled state, OFF time, and ON time all match.

The normal coordinator update remains a read-only state/RTC refresh. Schedule values are not repeatedly written when they are already verified.

Diagnostic sensors include:

- **Schedule status**
- **Programmed interval**
- **Last schedule verification**

## Version history

### v0.6.14

- Replaced the v0.6.13 custom duplicate-discovery guard with Home Assistant's native discovery-without-unique-ID mechanism.
- Automatic discovery now stops when a Nixie config entry already exists.
- Only one automatic Nixie discovery flow can be active while initial setup is pending.
- The actual Bluetooth address is assigned as unique ID only when the first discovered clock is confirmed.
- Manual setup remains available for intentionally adding additional physical clocks.
- Updated user-facing repository terminology to **Marketplace**.

### v0.6.13

- Added duplicate suppression for automatic Bluetooth discovery when a clock is rediscovered with another Bluetooth address.
- Prevented multiple simultaneous automatic discovery confirmation flows.
- Existing configured addresses were left unchanged.
- Manual setup remained available for additional clocks.

### v0.6.12

- Added an on-demand active Bluetooth scan when no proxy has a fresh advertisement or source-specific cache entry.
- Kept the per-scanner advertisement callback active during the scan.
- Rebuilt and RSSI-ranked the multi-proxy candidate list after the scan.
- The active scan does not establish an additional GATT connection.

### v0.6.11

- Added configurable regular Bluetooth polling from 1 to 360 minutes.
- Default polling remains 5 minutes.
- Interval changes are persisted and applied immediately.
- Renamed the automatic synchronization interval to **Time sync interval** to distinguish it from Bluetooth polling.

### v0.6.10

- Added configurable automatic clock synchronization interval from 1 to 24 hours.
- Default interval remains 24 hours.
- Manual synchronization does not change the automatic cadence.
- Added Marketplace metadata, Marketplace validation, and hassfest validation.

### v0.6.9

- Added automatic multi-proxy Bluetooth source selection.
- Collects fresh per-scanner advertisements and supplements them with source-specific cache entries.
- Ranks candidates by RSSI and falls back to the next source on connection failure.
- Expanded Bluetooth proxy diagnostics.

### v0.6.8

- Added the **Last used Bluetooth proxy** diagnostic sensor.

### v0.6.7

- Added non-blocking Bluetooth startup and 30-second retry after failed initial reads.
- Advanced scheduling waits for the first successful clock read.

### v0.6.6

- Added local Home Assistant brand artwork.

Historical documentation for v0.1.0 through v0.6.5 is preserved in [`history/`](history/README.md). Source snapshot branches are available for every preserved release from v0.1.0 through v0.6.14, excluding v0.6.1–v0.6.4 because no standalone packages were created for those versions.

## Changelog

See [`CHANGELOG.md`](CHANGELOG.md) for the complete version history.
