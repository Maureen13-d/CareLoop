# Hardware outline

This is a bill of materials and a firmware sketch for a later kit. It is **not** a diagnostic device, it is not certified, and it has not been verified against a Kenya regulatory filing. Nothing here should be built and used on a person from this document alone. Thresholds are PENDING CLINICAL REVIEW.

Cuffless wrist blood pressure is not used. The only blood-pressure input is a cuff reading typed or sent by the hub. The band can ask for that reading. It does not produce the red, yellow, or green label.

A published CHP kit list was not confirmed from a primary source for this prototype, so this page does not invent one.

## Hub

The hub is a box a promoter carries.

| Part | Role |
|---|---|
| ESP32-S3 | Wi-Fi and a small controller |
| Cuff with a manual or digital display | The promoter reads the numbers and enters them. The box does not interpret the cuff by itself |
| Urine strip and a colour card | Entered as neg, trace, 1+, 2+, 3+, or unknown |
| Haemoglobin band | Entered as normal, mild, moderate, severe, or unknown |
| Three lamps plus words | Green "usual day", yellow "navigator", red "go now". Colour is never the only signal |
| SIM module | SMS fallback when there is no data |
| Battery and a charge port | |

The hub stores a pseudonymous id such as `HUB-0007`. It does not store a name. It keeps a queue when the link is offline and sends it later. Sending the same client id twice is ignored.

Firmware, in outline only:

1. Show the booklet prompt and the three lamps with their words.
2. Accept the cuff numbers, the strip, and the toggles.
3. Compute a local label with the same thresholds as `rules/maternal_triage.yaml`, and show the word.
4. If the link is data, POST `/api/v1/device/readings` with `X-Device-Key`.
5. If the link is SMS, send the `R|...|checksum` line.
6. If the link is offline, keep the reading until the next data or SMS session.
7. Replace the local lamp if the server label differs. The server wins.

## Band

The band is lent, not owned by the software. It carries a pseudonymous id such as `BAND-0012`.

| Part | Role |
|---|---|
| Low-power MCU | Events only |
| Pulse sensor | May emit `hr_trend`. This does not change risk |
| Pulse oximeter | May emit `spo2_low`. This does not change risk |
| Motion | May emit `inactivity` |
| Battery gauge | May emit `battery_low` |
| Button | Emits `sos` |
| Vibrator | Plays a command from the server: vibrate, nudge a cuff reading, or ask for a check-in |

`sos` is the only band event that opens or escalates a journey. The other events create a promoter task or a command. Rules of thumb live in `rules/band_nudges.yaml` and are assumed.

## Regulatory note

This repository does not claim Kenya Pharmacy and Poisons Board clearance, a medical-device class, or a calibrated measurement. The web hub at `/hub` is a simulator of this sketch. It uses synthetic people.
