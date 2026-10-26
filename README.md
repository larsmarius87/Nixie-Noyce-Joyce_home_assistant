# Noyce Joyce Nixie – Home Assistant v0.6.0

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
- Retry hvert 5. minutt dersom tidsplanen ikke kan programmeres over BLE
- Sensor for neste planlagte hendelse
- Sensor for sist vellykkede klokkesynk
- Sensor for sist vellykkede BLE-kontakt

## Tidsplanmodus

`Enkel` er standard og lar klokka bruke sitt vanlige nattmodusintervall akkurat som før.

`Ukedag / helg` lar Home Assistant programmere neste relevante intervall til klokka. Helgeprofilen velges etter morgenen/display-på-dagen. Det betyr at fredag kveld bruker helgetiden for lørdag morgen, mens søndag kveld bruker ukedagstiden for mandag morgen.

Dagtidsavslag gjelder mandag–fredag. Siden klokkens firmware bare kan lagre ett nattmodusintervall om gangen, programmerer Home Assistant automatisk neste intervall etter at det forrige er ferdig. Klokka utfører selve av/på-hendelsen lokalt når intervallet allerede er programmert.

## Oppgradering

Kopier `custom_components/noyce_joyce_nixie` over eksisterende mappe og start Home Assistant på nytt.

Eksisterende innstillinger fra v0.4 beholdes. Avansert tidsplan starter i `Enkel`, så den endrer ikke klokkas oppførsel før du velger `Ukedag / helg`.


## RTC / drift measurement (v0.6.0)

The integration now attempts to read the clock's own RTC value from the Date/Time characteristic on every normal coordinator refresh (5 minutes). Two diagnostic sensors are exposed:

- **Klokkens tid** – the wall-clock time returned by the Nixie clock at the last read.
- **Klokkeavvik** – difference in seconds between the Nixie RTC and Home Assistant at the BLE read midpoint. Positive values mean the Nixie clock is ahead.

The read is optional/fail-safe: if a firmware variant does not permit reading the Date/Time characteristic, all other entities continue working.
