# Reverse-engineered BLE-protokoll

[Norsk](#norsk) · [English](#english)

## Norsk

Basis-UUID-suffiks: `-130A-4D4B-ACBA-5DE7E77E9B47`

| UUID | Betydning | Koding |
|---|---|---|
| A8ED1400... | Hovedtjeneste, egendefinert | Service |
| A8ED1410... | Dato/tid | 4-byte little-endian lokal Unix-lignende tidsverdi; lesing + skriving brukes for RTC-visning/synkronisering |
| A8ED1420... | Tidsformat | u8: 0 = 24 t, 1 = 12 t |
| A8ED1421... | Hourglass / anti-poisoning | u8: 0=1 min, 1=10 min, 2=30 min, 3=60 min, 4=24 t (vises som Off i HA) |
| A8ED1423... | Nattmodus aktivert | u8: 0/1 |
| A8ED1424... | Nattmodus display PÅ-tid | uint32 little-endian sekunder siden midnatt |
| A8ED1425... | Nattmodus display AV-tid | uint32 little-endian sekunder siden midnatt |
| A8ED1426... | Nixie-prikker | u8: 0/1 |
| A8ED14FF... | DFU/bootloader-relatert | brukes ikke til normal styring |

Firmware-revisjon er tilgjengelig via standard Device Information-characteristic `00002A26-0000-1000-8000-00805F9B34FB`.

Hourglass-mappingen ble bekreftet i firmware gjennom scheduler-betingelsene: hvert minutt, minutt mod 10, minutt mod 30, hver time og én gang daglig.

### Måling av RTC-avvik

Home Assistant-integrasjonen leser `A8ED1410...` og sammenligner den returnerte lokale epoch-verdien med forventet lokal epoch-verdi i Home Assistant ved midtpunktet av BLE-avlesningen. Dette kompenserer for mesteparten av forsinkelsen i BLE-transaksjonen. Siden enhetsverdien har ett sekunds oppløsning, bør avvik under ett sekund betraktes som omtrentlige.

### Kontrollavlesning av scheduler (v0.6.5)

Den avanserte scheduleren behandler `A8ED1423`, `A8ED1425` og `A8ED1424` som en verifisert triplet:

- `1423`: nattmodusmotor aktivert
- `1425`: display AV-tid
- `1424`: display PÅ-tid

Før et intervall programmeres, leser HA disse verdiene. Dersom de allerede samsvarer med ønsket intervall, skrives ingenting. Hvis skriving er nødvendig, bruker hver GATT-skriving `response=True`, etterfulgt av umiddelbar kontrollavlesning av alle tre characteristics. Tidsplanen markeres bare som verifisert når aktivert/start/slutt alle samsvarer med de ønskede verdiene. Nytt forsøk planlegges bare etter BLE-feil eller avvik ved kontrollavlesning.

---

## English

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

## Scheduler read-back verification (v0.6.5)

The advanced scheduler treats `A8ED1423`, `A8ED1425` and `A8ED1424` as a verified triplet:

- `1423`: night-mode engine enabled
- `1425`: display OFF time
- `1424`: display ON time

Before programming an interval, HA reads these values. If they already match the desired interval, no write is made. If a write is required, each GATT write uses `response=True`, followed by an immediate read-back of all three characteristics. A schedule is only marked verified when enabled/start/end all match the requested values. Retry is only scheduled after a BLE failure or a read-back mismatch.
