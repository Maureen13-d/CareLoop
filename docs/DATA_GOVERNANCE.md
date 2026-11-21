# Data governance

CareLoop in this prototype stores **synthetic** people only. See `docs/DATA_DECLARATION.md`.

## What this split is

Contacts (a phone number or a Telegram chat id) live in `contact_vault`, keyed by the public patient ID. Journey tables, the facility dashboard, the CHW worklist, and the audit log store the ID and labels. They do not store the contact.

`contact_for_send` in `backend/app/modules/followup/vault.py` is the only function that reads the vault. Check-ins call it so a message is not attempted when there is no contact. The contact is not copied into the message body or the audit log.

## What this split is not

This is **pseudonymisation, not anonymisation**. An ID together with a contact is still personal data. Someone who can read both tables can re-link them. A deployment would need access control, encryption, a retention schedule, and a lawful basis under Kenya's Data Protection Act. None of that is done here.

The simulated one-time code can be shown on a staff screen while `CARELOOP_EXPOSE_SIMULATED_CODES` is true. Turn that off before any real use. The code is still only a demo of a second check.

## Audit

Audit rows store the role, the action, and a label such as `danger_sign` or `contact_attempt`. They do not store what the person typed.

## Clinical wording

Danger-sign phrases and the lines the guide speaks are marked **PENDING CLINICAL REVIEW**. They are not a protocol.
