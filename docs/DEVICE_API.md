# Device API

Devices authenticate with the header `X-Device-Key`. They do not use a staff login. The demo key for HUB-0007 and the seeded band is `synthetic-device-key`. It is a prototype secret, not a production key.

All routes are under `/api/v1/device`. A reading is idempotent on the device id plus `client_reading_id`. A band event is idempotent on the device id plus `event_id`. More than 60 messages from one device in a minute returns 429.

The server recomputes the level. If the hub also sends `hub_local_level` and it differs, the audit stores both labels and the server label is the one that counts.

## POST /readings

```json
{
  "device_id": "HUB-0007",
  "client_reading_id": "HUB-0007-1",
  "pregnancy_ref": "the booklet reference",
  "systolic": 150,
  "diastolic": 96,
  "pulse": 80,
  "urine_protein": "neg",
  "hb_band": "normal",
  "danger_signs": ["headache_severe", "vision_blurred"],
  "hub_local_level": "yellow"
}
```

`urine_protein` is `neg`, `trace`, `1+`, `2+`, `3+`, or `unknown`. `hb_band` is `normal`, `mild`, `moderate`, `severe`, or `unknown`. Unknown and missing values are not green.

Yellow or red opens the maternal journey if needed and creates one `maternal_warning` task. A repeat of the same client id returns `"duplicate": true` and does not open a second journey.

## POST /sms-ingest

Body: `{ "text": "R|HUB-0007|1|150|96|80|0|HS|ab", "pregnancy_ref": "booklet" }`.

The line is `R|device|seq|systolic|diastolic|pulse|protein|signs|checksum`. The checksum is the sum of character codes of the text before the last pipe, modulo 256, as two hex digits. Protein codes are `0 t 1 2 3 u`. Sign codes are `H S B C A D F W L E M`. A bad checksum or an unknown code is rejected. The stored client id is the canonical device id plus the sequence, so `HUB0007` and `HUB-0007` match.

## POST /band/events

```json
{
  "device_id": "BAND-0012",
  "event_id": "evt-1",
  "type": "sos",
  "hr": null,
  "spo2": null,
  "battery_pct": 40
}
```

The band must be lent. `sos` opens one urgent journey and queues a discreet text. `hr_trend` and `spo2_low` create a cuff task and do not open a journey. `inactivity` queues a check-in command. `battery_low` creates a charge task. `ack` acknowledges the oldest command. Anything else is 422.

## GET /band/commands?device_id=BAND-0012

Returns unacknowledged commands: `vibrate`, `nudge_reading`, or `check_in`.

## POST /heartbeat

`{ "device_id": "HUB-0007", "battery_pct": 80 }` updates last-seen. A staff call to `POST /api/v1/maternal/devices/offline` opens at most one open "device offline" task when a device has been quiet longer than the assumed window in `rules/band_nudges.yaml`.

Staff can also record a reading, a check-in, a barrier, a simulated voucher, a simulated cover check, and a band lend or return under `/api/v1/maternal/`. Those routes use the staff login, not the device key. The audit for a check-in stores the level and the template id, not the words a woman typed.
