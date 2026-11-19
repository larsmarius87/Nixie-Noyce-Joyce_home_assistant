# Noyce Joyce Nixie – Home Assistant v0.6.14

[Norsk](#norsk) · [English](#english)

## Norsk

Lokal Bluetooth-integrasjon for Noyce Joyce Nixie Clock.

### Funksjoner

- Manuell synkronisering av klokken
- Automatisk synkronisering med konfigurerbart klokkeslett og intervall fra 1–24 timer
- Automatisk nytt forsøk etter 10 minutter dersom klokkesynkronisering feiler på grunn av Bluetooth
- 12/24-timers tidsformat
- Styring av Nixie-prikker
- Nattmodus
- Klokkens innebygde tidspunkter for av/på i nattmodus
- Hourglass / anti-poisoning-effekt
- Avansert tidsplan for ukedager og helg
- Valgfri avslått skjerm på dagtid mandag–fredag
- Automatisk programmering av neste relevante av/på-vindu inn i klokkens ene interne nattmodusintervall
- Kontrollavlesning etter skriving av tidsplan
- Tidsplanverdier skrives bare når verdiene som allerede ligger i klokken avviker fra ønsket tidsplan
- Nytt forsøk etter fem minutter bare ved Bluetooth-feil eller mislykket kontrollavlesning
- Diagnosesensorer for tidsplanstatus, programmert intervall og sist verifiserte tidsplan
- Sensor for neste planlagte hendelse
- Sensor for siste vellykkede klokkesynkronisering
- Sensor for siste vellykkede Bluetooth-kontakt
- Diagnosesensor for sist brukte Bluetooth-proxy/skanner, inkludert MAC-adresse og skannernavn når tilgjengelig
- Robust Bluetooth-oppstart: integrasjonen blokkerer ikke Home Assistant dersom klokken ikke kan nås under oppstart
- Automatisk valg mellom flere proxyer: ferske og bufrede Bluetooth-kilder rangeres etter RSSI, og neste kilde prøves dersom tilkoblingen feiler
- Aktiv Bluetooth-skanning som reserve når ingen proxy ser en annonsering fra klokken
- Automatisk undertrykking av duplikat-discovery når samme klokke observeres med skiftende Bluetooth-adresse
- Konfigurerbart ordinært Bluetooth-avlesningsintervall fra 1–360 minutter, standard 5 minutter

### Tidsplanmoduser

**Simple** er standardmodus og lar klokken bruke sitt vanlige innebygde nattmodusintervall.

**Weekday / weekend** lar Home Assistant programmere neste relevante intervall inn i klokken. Helgeprofilen velges ut fra dagen klokken skal slå på displayet om morgenen. Det betyr at fredag kveld bruker helgeprofilen for lørdag morgen, mens søndag kveld bruker ukedagsprofilen for mandag morgen.

Den valgfrie perioden med avslått display på dagtid gjelder mandag til fredag. Siden klokkens firmware bare kan lagre ett nattmodusintervall om gangen, programmerer Home Assistant automatisk neste intervall etter at det gjeldende er ferdig. Selve av/på-hendelsen utføres lokalt av klokken når intervallet først er programmert.

### Installer fra Marketplace

Repoet er klargjort for installasjon via Marketplace. Dersom det ennå ikke vises i vanlig Marketplace-søk, kan det legges til som et egendefinert repository:

1. Åpne **Marketplace → Integrations**.
2. Åpne menyen og velg **Custom repositories**.
3. Legg til `https://github.com/larsmarius87/Nixie-Noyce-Joyce_home_assistant`.
4. Velg kategorien **Integration**.
5. Installer **Noyce Joyce Nixie** og start Home Assistant på nytt.

For å bli tilgjengelig som et vanlig søkbart repository i Marketplace kreves det også en publisert GitHub Release og innsending til Marketplaces standardliste over repositories.

### Oppgradering

Ved installasjon gjennom Marketplace brukes den vanlige oppdateringsflyten i Marketplace.

Ved manuell installasjon erstatter du `custom_components/noyce_joyce_nixie` med den nye versjonen og starter Home Assistant på nytt.

Eksisterende konfigurasjon beholdes ved oppgradering. Den avanserte tidsplanen bruker **Simple** som standard dersom den ikke allerede er konfigurert.

### Beskyttelse mot duplikat Bluetooth-discovery (v0.6.14)

Fra v0.6.14 bruker integrasjonen Home Assistants innebygde discovery-håndtering i stedet for den egendefinerte duplikatbeskyttelsen som ble introdusert i v0.6.13.

- Automatisk Bluetooth-discovery bruker én midlertidig, delt discovery-identitet internt i Home Assistant.
- Dersom en Nixie-konfigurasjon allerede finnes, avbrytes nye automatiske discovery-forslag umiddelbart, selv om klokken annonseres med en annen Bluetooth-adresse.
- Dersom ingen Nixie er konfigurert, kan bare én automatisk discovery-flyt være aktiv om gangen.
- Den faktiske Bluetooth-adressen blir config entry-ens unique ID først når den første oppdagede klokken bekreftes.
- Bluetooth-adressen til en eksisterende config entry byttes aldri i bakgrunnen.
- Manuelt oppsett er fortsatt tilgjengelig for brukere som bevisst har mer enn én fysisk Nixie-klokke.
- Etter oppgradering fra v0.6.13 anbefales en full omstart av Home Assistant for å rydde discovery-flyter som allerede lå i minnet før oppdateringen.

### Aktiv Bluetooth-skanning som reserve (v0.6.12)

Når ingen Home Assistant-skanner/proxy har verken en fersk annonsering eller en kildespesifikk cacheoppføring for klokken, gjør integrasjonen ett ekstra discovery-forsøk før den gir opp:

1. Den vanlige tre sekunders innsamlingen av annonseringer kjøres først.
2. Hvis både ferske observasjoner og skannercache er tomme, ber integrasjonen Home Assistant om en kort aktiv Bluetooth-skanning.
3. Callback for annonseringer forblir registrert under skanningen slik at observasjoner fra alle skannere kan bli kandidater.
4. Kandidatlisten bygges på nytt og rangeres fortsatt etter RSSI.
5. Hvis klokken fremdeles ikke annonserer, overtar vanlig håndtering av tilkoblingsfeil og nytt forsøk.

Den aktive skanningen er **ikke en GATT-tilkobling til klokken**. Den brukes bare som reserve for å oppdage annonseringer og legger derfor ikke til en ekstra connect/disconnect-syklus.

Bluetooth-kildediagnosen viser `active scan: ...` når denne reservefunksjonen ble brukt.

### Bluetooth-avlesningsintervall (v0.6.11)

**Bluetooth update interval** styrer hvor ofte Home Assistant gjør den ordinære Bluetooth-tilkoblingen som brukes til å lese status og RTC fra klokken.

- Område: **1–360 minutter**
- Trinn: **1 minutt**
- Standard: **5 minutter**
- Verdien lagres i config entry og overlever omstarter.
- Endringer trer i kraft umiddelbart ved at coordinator-planen settes opp på nytt.
- Det separate 30-sekunders forsøket etter en mislykket coordinator-avlesning er uendret.
- Klokkesynkronisering bruker sin egen separate innstilling **Time sync interval**.

### Justerbart intervall for klokkesynkronisering (v0.6.10)

- **Auto sync** aktiverer eller deaktiverer automatisk klokkesynkronisering.
- **Auto sync time** brukes som første anker før den første vellykkede automatiske synkroniseringen.
- **Time sync interval** kan settes fra **1 til 24 timer** i hele timer. Standard: **24 timer**.
- Etter en vellykket automatisk synkronisering følger neste kjøring det valgte intervallet.
- Manuell synkronisering flytter ikke den automatiske tidsplanen.
- Dersom automatisk synkronisering feiler på grunn av Bluetooth, er nytt forsøk fortsatt etter **10 minutter**.
- Endring av ankeret for automatisk synkronisering nullstiller intervallankeret slik at det nye klokkeslettet brukes.

### Valg mellom flere Bluetooth-proxyer (v0.6.9)

Fra v0.6.9 bruker integrasjonen automatisk kildevalg mellom Home Assistants Bluetooth-skannere/proxyer:

1. Ferske annonseringer for klokkens MAC-adresse samles inn fra alle skannere i et kort innsamlingsvindu.
2. Home Assistants kildespesifikke skannercache legges til dersom en skanner ikke annonserte i dette vinduet.
3. Kandidatene rangeres strengt etter RSSI, sterkest først.
4. En fersk observasjon fra en kilde overstyrer bufret informasjon fra samme kilde.
5. Opptil seks Bluetooth-kilder prøves, med ett tilkoblingsforsøk per kilde.
6. Dersom den sterkeste kilden feiler, prøves neste kandidat automatisk.
7. Coordinatorens 30-sekunders retry brukes dersom ingen kandidat lykkes.

Ingen proxy er hardkodet eller låst.

Diagnosesensoren **Last used Bluetooth proxy** viser kilden som ble brukt for siste vellykkede Bluetooth-tilkobling, med attributter for skannernavn, RSSI, antall kandidater, antall fallback-forsøk, discovery-metode og rangert kandidatliste.

### Robust Bluetooth-oppstart (v0.6.7)

Den første Bluetooth-tilkoblingen er ikke lenger en del av den blokkerende oppstarten av config entry.

Dette er nyttig med ESPHome Bluetooth Proxy, der en skanner av og til kan ha en hengende eller opptatt tilkoblingsplass etter en omstart av Home Assistant.

Oppførsel:

1. Integrasjonen fullfører innlasting uten at klokken må være tilgjengelig under oppstart.
2. Entiteter som er avhengige av klokkedata forblir utilgjengelige frem til første vellykkede Bluetooth-avlesning.
3. Første avlesning starter i bakgrunnen.
4. Dersom tilkoblingen feiler, forblir integrasjonen lastet og coordinator prøver igjen etter **30 sekunder**.
5. Når klokken blir tilgjengelig, kommer entitetene tilbake automatisk.
6. Avansert tidsplanprogrammering venter til minst én gyldig klokkeavlesning er fullført, slik at konkurrerende Bluetooth-tilkoblinger under oppstart unngås.

Fra v0.6.11 kan normal polling konfigureres med **Bluetooth update interval** fra 1 til 360 minutter.

### RTC og måling av klokkeavvik (v0.6.0)

Integrasjonen leser klokkens RTC fra Date/Time-karakteristikken under ordinære coordinator-oppdateringer.

To diagnosesensorer vises:

- **Clock time** – klokkeslettet Nixie-klokken returnerte ved siste avlesning.
- **Clock drift** – differansen i sekunder mellom Nixie-klokkens RTC og Home Assistant ved midtpunktet for Bluetooth-avlesningen. Positive verdier betyr at Nixie-klokken går foran.

Avlesningen er fail-safe: dersom en firmwarevariant ikke tillater lesing av Date/Time-karakteristikken, fortsetter resten av integrasjonen å fungere.

### Verifisert tidsplan (v0.6.5)

I avansert **Weekday / weekend**-modus verifiseres programmering av tidsplanen ved kontrollavlesning:

1. Home Assistant leser først gjeldende verdier for Night mode, Display OFF og Display ON fra klokken.
2. Dersom verdiene allerede samsvarer med ønsket intervall, skrives ingenting.
3. Dersom de avviker, skrives de tre verdiene med GATT write response.
4. Integrasjonen leser umiddelbart verdiene tilbake fra klokken.
5. Tidsplanen markeres bare som vellykket når aktivert status, OFF-tid og ON-tid alle samsvarer.

Den normale coordinator-oppdateringen er fortsatt en ren leseoperasjon for status/RTC. Tidsplanverdier skrives ikke gjentatte ganger når de allerede er verifisert.

Diagnosesensorene inkluderer:

- **Schedule status**
- **Programmed interval**
- **Last schedule verification**

### Versjonshistorikk

#### v0.6.14

- Erstattet den egendefinerte duplikatbeskyttelsen fra v0.6.13 med Home Assistants innebygde discovery-håndtering uten unique ID.
- Automatisk discovery stopper nå når en Nixie config entry allerede finnes.
- Bare én automatisk Nixie-discovery-flyt kan være aktiv mens førstegangsoppsettet venter.
- Den faktiske Bluetooth-adressen settes som unique ID først når den første oppdagede klokken bekreftes.
- Manuelt oppsett er fortsatt tilgjengelig for bevisst å legge til flere fysiske klokker.
- Oppdaterte brukerrettet repository-terminologi til **Marketplace**.

#### v0.6.13

- La til undertrykking av duplikater ved automatisk Bluetooth-discovery når en klokke oppdages på nytt med en annen Bluetooth-adresse.
- Hindret flere samtidige automatiske discovery-bekreftelsesflyter.
- Eksisterende konfigurerte adresser ble beholdt uendret.
- Manuelt oppsett for ekstra klokker ble beholdt.

#### v0.6.12

- La til aktiv Bluetooth-skanning ved behov når ingen proxy har en fersk annonsering eller kildespesifikk cacheoppføring.
- Holdt callback for annonseringer aktiv under skanningen.
- Bygget kandidatlisten på nytt og rangerte den etter RSSI etter skanningen.
- Den aktive skanningen oppretter ikke en ekstra GATT-tilkobling.

#### v0.6.11

- La til konfigurerbar ordinær Bluetooth-polling fra 1 til 360 minutter.
- Standard polling er fortsatt 5 minutter.
- Intervallendringer lagres og brukes umiddelbart.
- Endret navnet på intervallet for automatisk klokkesynkronisering til **Time sync interval** for å skille det fra Bluetooth-polling.

#### v0.6.10

- La til konfigurerbart intervall for automatisk klokkesynkronisering fra 1 til 24 timer.
- Standardintervallet er fortsatt 24 timer.
- Manuell synkronisering endrer ikke den automatiske rytmen.
- La til metadata for Marketplace, Marketplace-validering og hassfest-validering.

#### v0.6.9

- La til automatisk valg mellom flere Bluetooth-kilder/proxyer.
- Samler ferske annonseringer per skanner og supplerer dem med kildespesifikke cacheoppføringer.
- Rangerer kandidater etter RSSI og faller tilbake til neste kilde ved tilkoblingsfeil.
- Utvidet Bluetooth-proxy-diagnostikk.

#### v0.6.8

- La til diagnosesensoren **Last used Bluetooth proxy**.

#### v0.6.7

- La til ikke-blokkerende Bluetooth-oppstart og nytt forsøk etter 30 sekunder ved mislykket første avlesning.
- Avansert tidsplan venter på første vellykkede klokkeavlesning.

#### v0.6.6

- La til lokale Home Assistant-brandbilder for integrasjonen.

Historisk dokumentasjon for v0.1.0 til og med v0.6.5 er bevart i [`history/`](history/README.md). Kilde-snapshot-branches finnes for alle bevarte utgivelser fra v0.1.0 til og med v0.6.14, med unntak av v0.6.1–v0.6.4 fordi det ikke ble laget egne pakker for disse versjonene.

### Endringslogg

Se [`CHANGELOG.md`](CHANGELOG.md) for komplett versjonshistorikk.

---

## English

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
