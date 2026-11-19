# Data Policy

CareLoop is a hackathon MVP. **Synthetic data only.**

- No real patient data, PHI, or PII may be committed, uploaded, or processed.
- All patient references must match `SYN-<digits>` (enforced in `backend/app/models.py`).
- SLA durations in `backend/app/pathway.py` are **placeholders** and have not been clinically reviewed.
- This software is not a medical device and must not be used for clinical decisions.

## Database
- The SQLite file is gitignored. Never commit database files.
- `patient_ref` is constrained to `SYN-<digits>` by a database CHECK constraint, in addition to
  application-level validation, so direct SQL inserts of other identifiers are rejected.

## Metrics
Metrics are computed from synthetic data and are illustrative only. They must not be presented as
evidence of real-world effectiveness, and SLA targets used in them are unverified placeholders.
