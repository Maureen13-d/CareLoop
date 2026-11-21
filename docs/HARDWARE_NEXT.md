# Hardware next (not in this build)

An optional later kit, for a community health worker who screens away from the network.

## What it would do

- A small screening station records the same fields as the web form: age band, area, screening type, finding, consent, language, channel.
- If the finding is concerning or urgent and the person consents, the station issues the same public ID and prints the slip: ID, a QR of the ID only, three plain lines. No condition. No contact on the paper.
- The contact is kept in an encrypted queue on the device.
- When the station sees a network, it syncs the queue to CareLoop. The journey opens then, not before.
- Offline, the station can still hand the person the slip. It cannot send the one-time code until it syncs.

## What it is not

This file is a note for a later pilot. There is no device firmware, no printer driver, and no offline database in this repository. The maternal hub and band described in `docs/HARDWARE.md` are a different, earlier idea and are not this station.
