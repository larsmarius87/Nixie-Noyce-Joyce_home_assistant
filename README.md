# Noyce Joyce Nixie – Home Assistant v0.6.8

Lokal Bluetooth-integrasjon for Noyce Joyce Nixie Clock.

## Funksjoner

- Synkroniser klokke manuelt
- Automatisk daglig klokkesynk med justerbart tidspunkt
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

## Tidsplanmodus

`Enkel` er standard og lar klokka bruke sitt vanlige nattmodusintervall akkurat som før.

`Ukedag / helg` lar Home Assistant programmere neste relevante intervall til klokka. Helgeprofilen velges etter morgenen/display-på-dagen. Det betyr at fredag kveld bruker helgetiden for lørdag morgen, mens søndag kveld bruker ukedagstiden for mandag morgen.

Dagtidsavslag gjelder mandag–fredag. Siden klokkens firmware bare kan lagre ett nattmodusintervall om gangen, programmerer Home Assistant automatisk neste intervall etter at det forrige er ferdig. Klokka utfører selve av/på-hendelsen lokalt når intervallet allerede er programmert.

## Oppgradering

Kopier `custom_components/noyce_joyce_nixie` over eksisterende mappe og start Home Assistant på nytt.

Eksisterende innstillinger fra v0.4 beholdes. Avansert tidsplan starter i `Enkel`, så den endrer ikke klokkas oppførsel før du velger `Ukedag / helg`.

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

## Changelog

See [`CHANGELOG.md`](CHANGELOG.md) for version history.
