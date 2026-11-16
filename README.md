# Noyce Joyce Nixie – Home Assistant v0.6.10

Lokal Bluetooth-integrasjon for Noyce Joyce Nixie Clock.

## Funksjoner

- Synkroniser klokke manuelt
- Automatisk klokkesynk med justerbart tidspunkt og intervall på 1–24 timer
- Automatisk retry hvert 10. minutt dersom klokkesynk feiler på grunn av BLE
- 12/24-timersformat
- Nixie-prikker
- Nattmodus
- Klokkens egne nattmodus start/slutt-tider
- Timeglasseffekt / anti-poisoning
- Avansert tidsplan med egne tider for ukedag og helg
- Valgfritt dagtidsavslag mandag–fredag
- Automatisk programmering av neste relevante av/på-vindu til klokkens ene interne nattmodusintervall
- Read-back-verifisering av tidsplanen etter BLE-skriving
- Skriver bare tidsplan når klokkens lagrede verdier faktisk avviker
- Retry hvert 5. minutt kun ved BLE-feil eller mislykket read-back-verifisering
- Sensorer for tidsplanstatus, programmert intervall og sist bekreftet tidsplan
- Sensor for neste planlagte hendelse
- Sensor for sist vellykkede klokkesynk
- Sensor for sist vellykkede BLE-kontakt
- Diagnostikksensor for sist brukte Bluetooth-proxy/scanner (MAC-adresse, med navn som attributt når tilgjengelig)
- Robust BLE-oppstart: integrasjonen blokkerer ikke Home Assistant dersom Bluetooth-proxyen ikke kan koble til ved restart
- Automatisk multi-proxyvalg: rangerer ferske og cachede Bluetooth-kilder etter RSSI og prøver neste kilde ved feil

## Tidsplanmodus

`Enkel` er standard og lar klokka bruke sitt vanlige nattmodusintervall akkurat som før.

`Ukedag / helg` lar Home Assistant programmere neste relevante intervall til klokka. Helgeprofilen velges etter morgenen/display-på-dagen. Det betyr at fredag kveld bruker helgetiden for lørdag morgen, mens søndag kveld bruker ukedagstiden for mandag morgen.

Dagtidsavslag gjelder mandag–fredag. Siden klokkens firmware bare kan lagre ett nattmodusintervall om gangen, programmerer Home Assistant automatisk neste intervall etter at det forrige er ferdig. Klokka utfører selve av/på-hendelsen lokalt når intervallet allerede er programmert.

## Installere med HACS

Repoet er klargjort som en HACS-integrasjon. Når GitHub-repoet er satt til **Public**, kan det legges til i HACS som et egendefinert repository:

1. Åpne **HACS → Integrasjoner**.
2. Åpne menyen og velg **Egendefinerte repositories / Custom repositories**.
3. Legg inn `https://github.com/larsmarius87/Nixie-Noyce-Joyce_home_assistant`.
4. Velg kategori **Integration**.
5. Installer **Noyce Joyce Nixie** og restart Home Assistant.

For å bli søkbar som et standardrepository i HACS Marketplace kreves i tillegg en full GitHub Release og innsending til `hacs/default`.

## Oppgradering

Kopier `custom_components/noyce_joyce_nixie` over eksisterende mappe og start Home Assistant på nytt.

Eksisterende innstillinger fra v0.4 beholdes. Avansert tidsplan starter i `Enkel`, så den endrer ikke klokkas oppførsel før du velger `Ukedag / helg`.

## Justerbart synkintervall (v0.6.10)

- **Auto-synk** slår automatisk klokkesynk av/på.
- **Tidspunkt for auto-synk** brukes som start/ankertidspunkt før første vellykkede automatiske synk.
- **Synkintervall** kan settes fra **1 til 24 timer** i hele timer. Standard er **24 timer**.
- Etter en vellykket automatisk synk planlegges neste synk etter valgt intervall.
- Manuell **Synkroniser klokke** endrer ikke den automatiske intervallplanen.
- Hvis en automatisk synk feiler over Bluetooth, beholdes eksisterende retry etter **10 minutter**.
- Endrer du **Tidspunkt for auto-synk**, nullstilles intervallets anker slik at det nye tidspunktet brukes.

## Multi-proxy Bluetooth-valg (v0.6.9)

Fra v0.6.9 bruker Nixie-integrasjonen samme grunnprinsipp for Bluetooth-kildevalg som Xzense 0.5.24:

1. Samler ferske annonseringer for klokkens MAC fra alle Home Assistant-scannere/proxyer i et kort vindu.
2. Supplerer med Home Assistants kildebestemte scanner-cache dersom en proxy ikke annonserte akkurat i innsamlingsvinduet.
3. Rangerer kandidatene strengt etter RSSI, sterkeste først.
4. Fersk observasjon fra en kilde overstyrer cache fra samme kilde.
5. Prøver opptil seks ulike Bluetooth-kilder, ett BLE-forsøk per kilde.
6. Hvis sterkeste kilde feiler, prøves neste kandidat automatisk.
7. Eksisterende 30-sekunders coordinator-retry brukes dersom ingen kandidat lykkes.

Ingen proxy er hardkodet eller låst. Hvis `bluetooth proxy stue` fysisk er nærmest klokka, skal den normalt velges automatisk når den også har sterkest RSSI.

Diagnostikksensoren **Sist brukt Bluetooth-proxy** viser fortsatt MAC/source for siste vellykkede BLE-forbindelse og har fra v0.6.9 også attributter for scanner-navn, RSSI ved tilkobling, antall kandidater, antall fallbacks, kildevalg og kandidatlisten.

## Robust BLE-oppstart (v0.6.7)

Fra v0.6.7 er første BLE-tilkobling **ikke lenger en del av den blokkerende config-entry-oppsettingen**.

Dette er spesielt nyttig med ESPHome Bluetooth Proxy, der en proxy i enkelte situasjoner kan ha en midlertidig stale/busy connection-slot etter restart av Home Assistant.

Oppførselen er nå:

1. Noyce Joyce-integrasjonen lastes ferdig uten å vente på at klokka må kunne kobles til akkurat under HA-oppstart.
2. Entiteter som krever klokkedata vises som utilgjengelige frem til første vellykkede BLE-avlesning.
3. Første BLE-avlesning startes umiddelbart i bakgrunnen.
4. Hvis tilkoblingen feiler, beholdes integrasjonen lastet og coordinatoren prøver igjen etter **30 sekunder**.
5. Når klokka blir tilgjengelig, går entitetene automatisk tilbake til normal tilstand.
6. Avansert tidsplan/scheduler venter med BLE-programmering til minst én gyldig avlesning fra klokka er mottatt. Dette hindrer parallelle connect-forsøk ved oppstart.

Dette endrer ikke vanlig polling etter at klokka er tilgjengelig; normal coordinator-oppdatering er fortsatt hvert 5. minutt.

## RTC / drift measurement (v0.6.0)

The integration now attempts to read the clock's own RTC value from the Date/Time characteristic on every normal coordinator refresh (5 minutes). Two diagnostic sensors are exposed:

- **Klokkens tid** – the wall-clock time returned by the Nixie clock at the last read.
- **Klokkeavvik** – difference in seconds between the Nixie RTC and Home Assistant at the BLE read midpoint. Positive values mean the Nixie clock is ahead.

The read is optional/fail-safe: if a firmware variant does not permit reading the Date/Time characteristic, all other entities continue working.

## Bekreftet scheduler (v0.6.5)

I avansert `Ukedag / helg`-modus er scheduler-logikken nå bekreftelsesbasert:

1. Home Assistant leser først `Night mode`, `Display OFF` og `Display ON` fra klokka.
2. Hvis verdiene allerede tilsvarer ønsket neste intervall, sendes ingen ny skriving.
3. Hvis de avviker, skrives de tre verdiene med GATT `response=True`.
4. Integrasjonen leser deretter de tre verdiene tilbake fra klokka og sammenligner dem med det som skulle programmeres.
5. Kun en bekreftet match regnes som vellykket. Ved BLE-feil eller mismatch prøves det på nytt etter 5 minutter.

Den ordinære coordinator-oppdateringen hvert 5. minutt er fortsatt en **lesing** av klokkas tilstand/RTC. Scheduler-verdiene sendes ikke på nytt hvert 5. minutt når de allerede er bekreftet.

Nye diagnostikksensorer:

- **Tidsplanstatus** – `Bekreftet`, `Kontrollerer`, `Ikke bekreftet – prøver igjen` eller `Enkel modus`.
- **Programmert intervall** – siste intervall som er lest tilbake og bekreftet, f.eks. `Natt 23:30–06:30`.
- **Sist tidsplan bekreftet** – tidspunkt for siste vellykkede read-back-verifisering.

## v0.6.10

- Added adjustable **Synkintervall** configuration from 1 to 24 hours.
- Default interval remains 24 hours.
- The configured auto-sync time is used as the initial anchor.
- After a successful automatic synchronization, future runs follow the selected interval.
- Manual clock synchronization does not shift the automatic schedule.
- Automatic retries after BLE failures still run after 10 minutes.
- Added HACS metadata, HACS validation workflow and hassfest workflow.
- Added required HACS manifest metadata: documentation, issue tracker and code owner.

## v0.6.9

- Added automatic multi-proxy Bluetooth source selection based on the proven Xzense 0.5.24 strategy.
- Collects per-scanner fresh advertisements and supplements them with Home Assistant's source-specific scanner cache.
- Ranks candidates strictly by RSSI and tries the next source when a BLE connection fails.
- Tries at most six sources per connection round and one Bleak connection attempt per source.
- Expanded `Sist brukt Bluetooth-proxy` diagnostics with RSSI, candidate count, fallback count, discovery method and ranked candidate details.
- Keeps the v0.6.7 30-second coordinator retry when no Bluetooth source succeeds.

## v0.6.8

- Added **Sist brukt Bluetooth-proxy** diagnostic sensor.
- Sensor state is the source/MAC of the scanner that carried the most recent successful BLE connection.
- Proxy/scanner name is exposed as an attribute when available.
- The last known proxy remains visible while the clock is temporarily unavailable.

## v0.6.7

- Non-blocking BLE startup.
- 30-second retry after failed initial BLE reads.
- Scheduler waits for the first successful clock read before programming an interval.

## v0.6.6

- Added local Home Assistant brand artwork (`brand/icon.png`, `icon@2x.png`, `logo.png`, `logo@2x.png`).

## Version history

Historical README and protocol documentation for v0.1.0 through v0.6.5 is preserved in [`history/`](history/README.md). Source snapshot branches are available for every preserved version: `v0.1.0`, `v0.2.0`, `v0.3.0`, `v0.4.0`, `v0.5.0`, `v0.6.0`, `v0.6.5`, `v0.6.6`, `v0.6.7`, `v0.6.8`, `v0.6.9` and `v0.6.10`.

## Changelog

See [`CHANGELOG.md`](CHANGELOG.md) for version history.
