# Data Policy

CareLoop is a hackathon MVP. **Synthetic data only.**

- No real patient data, PHI, or PII may be committed, uploaded, or processed.
- All patient references must match `SYN-<digits>` (enforced in `backend/app/models.py`).
- SLA durations in `backend/app/pathway.py` are **placeholders** and have not been clinically reviewed.
- This software is not a medical device and must not be used for clinical decisions.
