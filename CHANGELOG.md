# Endringslogg / Changelog

[Norsk](#norsk) · [English](#english)

## Norsk

Alle viktige endringer i Noyce Joyce Nixie-integrasjonen for Home Assistant dokumenteres her.

### 0.6.14

- Erstattet den egendefinerte duplikat-discovery-logikken fra v0.6.13 med Home Assistants innebygde `_async_handle_discovery_without_unique_id()`-håndtering.
- Automatisk Bluetooth-discovery avbrytes nå dersom en Nixie config entry allerede finnes, uavhengig av hvilken BLE-adresse som observeres.
- Home Assistant tillater bare én ventende automatisk discovery-flyt når ingen Nixie ennå er konfigurert.
- Den faktiske BLE-adressen settes som unique ID først etter at brukeren bekrefter den første oppdagede klokken.
- Eksisterende konfigurerte BLE-adresser erstattes aldri automatisk.
- Manuelt oppsett er fortsatt tilgjengelig for brukere som bevisst har flere fysiske Nixie-klokker.
- Oppdaterte brukerrettet repository-terminologi til **Marketplace**, samtidig som nødvendige tekniske identifikatorer som `hacs.json` og `hacs/action@main` beholdes.

### 0.6.13

- La til duplikatbeskyttelse for automatisk Bluetooth-discovery når en Nixie-klokke oppdages på nytt med en annen BLE-adresse.
- Automatisk duplikatbeskyttelse krever kjent Nixie service UUID og, når lokalt navn finnes, forventet navn `Nixie Clock`.
- Hindrer flere samtidige automatiske discovery-bekreftelsesflyter for samme type Nixie-enhet.
- Eksisterende config entries beholder lagret Bluetooth-adresse; discovery erstatter den ikke automatisk.
- Manuelt oppsett ble beholdt slik at brukere med flere fysiske Nixie-klokker fortsatt kan legge til en ekstra klokke med vilje.

### 0.6.12

- La til aktiv Bluetooth-skanning ved behov når verken ferske annonseringer eller kildespesifikke cacheoppføringer finnes for Nixie-klokken.
- Eksisterende callback for annonseringer forblir registrert under aktiv skanning slik at observasjoner fra alle skannere/proxyer fanges opp.
- Kandidat-discovery kjøres på nytt etter skanningen og rangerer fortsatt kildene strengt etter RSSI.
- Aktiv skanning oppretter ikke en GATT-tilkobling til klokken; vanlig multi-proxy-tilkobling er uendret.
- La til diagnostiske kildetekster som viser når active-scan fallback ble brukt.
- Eksisterende retry-tid for coordinator og automatisk klokkesynkronisering er uendret.

### 0.6.11

- La til konfigurerbart ordinært Bluetooth-pollingintervall fra 1 til 360 minutter.
- La til tallentiteten **Bluetooth update interval** i minutter.
- Standard ordinært pollingintervall er fortsatt 5 minutter.
- Intervallendringer lagres og brukes umiddelbart ved å planlegge DataUpdateCoordinator på nytt.
- Endret navn på intervallet for automatisk klokkesynkronisering fra **Sync interval** til **Time sync interval** for å unngå forveksling med BLE-polling.
- Beholdt separat nytt forsøk etter 30 sekunder ved mislykket coordinator-BLE-avlesning.

### 0.6.10

- La til konfigurerbart intervall for automatisk klokkesynkronisering fra 1 til 24 timer.
- Standardintervallet er 24 timer, som tidligere.
- La til tallentiteten **Sync interval** i timer.
- Konfigurert auto-sync-tid fungerer som første anker; senere automatiske kjøringer bruker valgt intervall.
- Manuell synkronisering endrer ikke rytmen for automatisk synkronisering.
- Endring av auto-sync-ankeret nullstiller rytmen slik at det nye klokkeslettet respekteres.
- Eksisterende 10-minutters BLE-retry etter mislykket automatisk synkronisering er beholdt.
- La til `hacs.json` og Marketplace-valideringsworkflow.
- La til hassfest-valideringsworkflow.
- La til `documentation`, `issue_tracker`, `codeowners` og `integration_type` i `manifest.json` for Marketplace/offentlig repository-klargjøring.

### 0.6.9

- Erstattet enkeltoppslaget med `async_ble_device_from_address()` med automatisk valg mellom flere Bluetooth-proxykilder.
- Bruker Home Assistant `async_register_advertisement_callback()` for å samle ferske annonseringer per skanner for klokken.
- Supplerer ferske observasjoner med `async_scanner_devices_by_address()` fra kildespesifikk skannercache.
- Rangerer kandidater strengt etter RSSI, sterkest først.
- Ferske observasjoner overstyrer cacheoppføringer fra samme skanner.
- Prøver opptil seks Bluetooth-kilder per tilkoblingsrunde og går videre til neste kilde ved feil.
- Bruker ett Bleak-tilkoblingsforsøk per kilde for å unngå nestede/aggressive retry-løkker.
- Beholder coordinatorens 30-sekunders retry fra v0.6.7 dersom alle kilder feiler eller klokken midlertidig ikke sees.
- Utvidet attributtene til **Last used Bluetooth proxy** med RSSI ved tilkobling, antall kandidater, fallback-antall, discovery-metode og rangert kandidatinformasjon.

### 0.6.8

- La til diagnosesensoren **Last used Bluetooth proxy**.
- Sporer skanner/proxy-kilden som faktisk bar siste vellykkede BLE-tilkobling, ikke bare siste kilde som annonserte.
- Bruker proxy/skanner-kilden, normalt MAC-adressen, som sensorstatus.
- Legger til proxy/skanner-navn som attributt når Home Assistant leverer det.
- Beholder siste kjente kilde synlig mens klokken midlertidig er frakoblet.

### 0.6.7

- Endret oppstart slik at integrasjonen ikke lenger blokkerer config-entry-oppsettet på første BLE-tilkobling.
- La til sikre placeholder-data i coordinator slik at entitetsplattformene kan lastes før klokken er tilgjengelig.
- Første BLE-refresh kjører nå i bakgrunnen etter at entitetsplattformene er satt opp.
- Mislykkede BLE-refresh ber om nytt forsøk etter 30 sekunder via Home Assistants DataUpdateCoordinator i stedet for å la config entry stå i setup retry.
- BLE-avhengig avansert tidsplanprogrammering utsettes til første vellykkede klokkeavlesning.
- Avansert tidsplanstatus viser **Waiting for clock** mens den venter på første vellykkede BLE-avlesning.
- Dette forbedrer gjenoppretting etter Home Assistant-omstart når en ESPHome Bluetooth Proxy midlertidig har en hengende eller opptatt tilkoblingsplass.

### 0.6.6

- La til lokale Home Assistant-brandbilder for integrasjonen.
- La til `brand/icon.png` og `brand/icon@2x.png`.
- La til `brand/logo.png` og `brand/logo@2x.png`.
- Oppdaterte pakkemetadata til versjon 0.6.6.

### 0.6.5

- Bygget om den avanserte tidsplanen til å bruke kontrollavlesning.
- Home Assistant leser nå klokkens gjeldende nattmodusinnstillinger før skriving.
- Tidsplanverdier skrives bare når lagrede verdier i klokken avviker fra ønsket intervall.
- BLE-skriving bruker GATT write response og etterfølges av umiddelbar kontrollavlesning.
- En tidsplan markeres bare som vellykket når nattmodus, av-tid og på-tid alle samsvarer.
- Fjernet ubetinget gjentatt skriving av tidsplan hvert femte minutt.
- Fem-minutters retry brukes nå bare etter BLE-feil eller mislykket kontrollavlesning.
- La til diagnosesensorer for tidsplanstatus, programmert intervall og tidspunkt for siste verifiserte tidsplan.
- Tilbakestilling til **Simple**-modus verifiseres også med kontrollavlesning.

### 0.6.0

- La til avlesning av Nixie-klokkens egen RTC over BLE.
- La til diagnosesensoren `Klokkens tid`.
- La til diagnosesensoren `Klokkeavvik`, som viser differansen mellom klokkens RTC og Home Assistant i sekunder.
- Bruker midtpunktet av BLE-avlesningen ved beregning av klokkeavvik for å redusere feil fra transaksjonsforsinkelse.
- RTC-avlesningen er fail-safe, slik at resten av integrasjonen fortsetter å fungere dersom en firmwarevariant ikke kan leses.

### 0.5.0

- La til avansert displaytidsplan.
- La til tidsplanmodusene **Simple** og **Weekday / weekend**.
- La til separate av- og på-tider for ukedager.
- La til separate av- og på-tider for helg.
- La til valgfri avslått displayperiode på dagtid mandag–fredag.
- Home Assistant programmerer dynamisk klokkens ene interne nattmodusintervall med neste relevante displayvindu.
- Helgevalg følger dagen for morgen/display-på, slik at fredag kveld bruker lørdagsprofilen og søndag kveld bruker mandagsprofilen.
- La til sensor for neste planlagte hendelse.
- La til sensor for siste vellykkede klokkesynkronisering.
- La til sensor for siste vellykkede BLE-kontakt.
- La til retry-håndtering for mislykkede Bluetooth-operasjoner.
- La til gjenoppretting av opprinnelig enkelt nattmodusintervall ved retur til **Simple**-modus.

### 0.4.0

- La til konfigurasjonsbryteren **Auto sync**.
- La til justerbar tidsentitet **Auto sync time**.
- Innstillinger for automatisk synkronisering beholdes gjennom omstarter av Home Assistant.
- Standard automatisk synkronisering er fortsatt aktiv kl. 04:05.
- Manuell knapp **Synchronize clock** beholdt.

### 0.3.0

- Forbedret presentasjonen av Hourglass / anti-poisoning.
- Firmwarens én-gang-per-døgn-modus vises som **Off** i Home Assistant, siden dette er den minst inngripende innstillingen.
- Tilgjengelige moduser: Off/én gang daglig, hvert minutt, hvert 10. minutt, hvert 30. minutt og hver time.

### 0.2.0

- La til manuell klokkesynkronisering fra Home Assistant.
- La til automatisk daglig klokkesynkronisering.
- La til tidssone-/sommertidsbevisst konvertering av lokal tid for RTC-synkronisering.
- Første automatiske synkroniseringstid satt til 04:05.

### 0.1.0

- Første egendefinerte Home Assistant-integrasjon basert på reverse engineering av Noyce Joyce Android-appen og medfølgende firmware.
- La til Bluetooth-discovery og tilkoblingsstøtte.
- La til sensor for firmware-revisjon.
- La til styring av 12/24-timers format.
- La til styring av Nixie-prikker.
- La til styring av Night Mode.
- La til tidsstyring for Night Mode display på/av.
- La til intervallstyring for Hourglass / anti-poisoning.
- Dokumenterte reverse-engineered BLE service- og characteristic-UUID-er.

---

## English

All notable changes to the Noyce Joyce Nixie Home Assistant integration are documented here.

## 0.6.14

- Replaced the v0.6.13 custom duplicate-discovery logic with Home Assistant's native `_async_handle_discovery_without_unique_id()` flow handling.
- Automatic Bluetooth discovery now aborts whenever a Nixie config entry already exists, regardless of the newly observed BLE address.
- Home Assistant permits only one pending automatic discovery flow when no Nixie has been configured yet.
- The actual BLE address is assigned as the config entry unique ID only after the user confirms the first discovered clock.
- Existing configured BLE addresses are never silently replaced.
- Manual setup remains available for users who intentionally have multiple physical Nixie clocks.
- Updated user-facing repository terminology to **Marketplace** while preserving required technical identifiers such as `hacs.json` and `hacs/action@main`.

## 0.6.13

- Added duplicate suppression for automatic Bluetooth discovery when a Nixie clock is rediscovered with a different BLE address.
- Automatic duplicate suppression requires the known Nixie service UUID and, when a local name is present, the expected `Nixie Clock` name.
- Prevents multiple simultaneous automatic discovery confirmation flows for the same Nixie device type.
- Existing config entries keep their stored Bluetooth address; discovery does not silently replace it.
- Manual setup remains available so users with multiple physical Nixie clocks can still add another device intentionally.

## 0.6.12

- Added an on-demand Home Assistant active Bluetooth scan when neither fresh advertisements nor source-specific scanner cache entries exist for the Nixie clock.
- The existing advertisement callback remains registered during the active scan so observations from all scanners/proxies are captured.
- Candidate discovery is repeated after the scan and continues to rank sources strictly by RSSI.
- Active scanning does not establish a GATT connection to the clock; normal multi-proxy connection behavior is unchanged.
- Added diagnostic source labels showing when the active-scan fallback was used.
- Existing coordinator retry timing and automatic time-sync retry behavior remain unchanged.

## 0.6.11

- Added configurable regular Bluetooth polling interval from 1 to 360 minutes.
- Added **Bluetooth update interval** number entity in minutes.
- Default regular polling interval remains 5 minutes.
- Interval changes are persisted and applied immediately by rescheduling DataUpdateCoordinator polling.
- Renamed the automatic clock synchronization interval entity from **Sync interval** to **Time sync interval** to avoid confusion with BLE polling.
- Preserved the separate 30-second retry after failed coordinator BLE reads.

## 0.6.10

- Added configurable automatic clock synchronization interval from 1 to 24 hours.
- Default interval is 24 hours, preserving previous behavior.
- Added **Sync interval** number entity in hours.
- The configured auto-sync time acts as the initial anchor; subsequent automatic runs use the selected interval.
- Manual synchronization does not change the automatic interval cadence.
- Changing the auto-sync anchor time resets the cadence so the new time is respected.
- Existing 10-minute BLE retry after failed automatic synchronization is preserved.
- Added `hacs.json` and Marketplace validation workflow.
- Added hassfest validation workflow.
- Added `documentation`, `issue_tracker`, `codeowners`, and `integration_type` to `manifest.json` for Marketplace/public repository readiness.

## 0.6.9

- Replaced the single cached `async_ble_device_from_address()` lookup with automatic multi-proxy source selection.
- Uses Home Assistant `async_register_advertisement_callback()` to collect fresh per-scanner advertisements for the clock.
- Supplements fresh observations with `async_scanner_devices_by_address()` source-specific cache entries.
- Ranks candidates strictly by RSSI, strongest first.
- Fresh observations override cache entries from the same scanner.
- Tries up to six Bluetooth sources per connection round and falls back to the next source on connection failure.
- Uses one Bleak connection attempt per source to avoid nested/aggressive retry loops.
- Preserves the v0.6.7 coordinator-level 30-second retry if all sources fail or the clock is temporarily not seen.
- Expanded **Last used Bluetooth proxy** attributes with RSSI at connection, candidate count, fallback count, source discovery method, and ranked candidate details.

## 0.6.8

- Added **Last used Bluetooth proxy** diagnostic sensor.
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
- Advanced schedule status shows **Waiting for clock** while waiting for the first successful BLE read.
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
- Restoring **Simple** schedule mode is also read-back verified.

## 0.6.0

- Added reading of the Nixie clock's own RTC over BLE.
- Added `Klokkens tid` diagnostic sensor.
- Added `Klokkeavvik` diagnostic sensor showing the difference between the clock RTC and Home Assistant in seconds.
- BLE read midpoint is used when calculating clock drift to reduce transaction-latency error.
- RTC reading is fail-safe so the rest of the integration continues working if a firmware variant cannot be read.

## 0.5.0

- Added advanced display scheduling.
- Added **Simple** and **Weekday / weekend** schedule modes.
- Added separate weekday display-off and display-on times.
- Added separate weekend display-off and display-on times.
- Added optional daytime display-off period for Monday through Friday.
- Home Assistant dynamically programs the clock's single internal night-mode interval with the next relevant display window.
- Weekend selection follows the morning/display-on day, so Friday night uses the Saturday profile and Sunday night uses the Monday profile.
- Added next scheduled event sensor.
- Added last successful clock sync sensor.
- Added last successful BLE contact sensor.
- Added retry handling for failed Bluetooth operations.
- Added restoration of the original simple night-mode interval when returning to **Simple** mode.

## 0.4.0

- Added **Auto sync** configuration switch.
- Added adjustable **Auto sync time** time entity.
- Automatic sync settings persist across Home Assistant restarts.
- Default automatic sync remains enabled at 04:05.
- Manual **Synchronize clock** button retained.

## 0.3.0

- Refined Hourglass / anti-poisoning presentation.
- The firmware's once-per-day mode is shown as **Off** in Home Assistant as the least intrusive option.
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
