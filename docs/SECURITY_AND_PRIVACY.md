# Security and Privacy

Status: design principles. CareLoop is a hackathon prototype using **synthetic data only**. It has had **no security audit and no legal review**, and makes no compliance claims.

## Principles

1. **Synthetic data only.** No real patient information is entered, stored, logged or committed, including in git history.
2. **Data minimisation.** Collect and show only what each step and role needs.
3. **Purpose-specific, revocable consent.** Consent is recorded per patient and purpose, and can be withdrawn.
4. **Least privilege.** Each role sees and does only what it needs.
5. **Everything is auditable.** State changes, case access and AI drafts are logged.
6. **Humans decide.** Software tracks and drafts; people make clinical, closure and escalation decisions.
7. **Fail safe.** If something is uncertain, slow or malformed, the system hands over to a person.

## Roles and permissions (demo design)

| Capability | Coordinator | Clinician | Program manager | Admin |
|---|---|---|---|---|
| View case worklist and detail | Yes | Yes | Aggregates only | No |
| Move case between stages | Yes (non-clinical stages) | Yes | No | No |
| Record evidence / close case | Evidence only | Yes | No | No |
| Create and approve patient message drafts | Yes | Yes | No | No |
| Handle escalations | Yes | Yes | No | No |
| View metrics | Yes | Limited | Yes | Yes |
| View audit log | No | No | Yes | Yes |
| Manage users and demo settings | No | No | No | Yes |

The exact stage permissions will be fixed in the pathway configuration. This matrix is a design choice for the demo, not a description of any real hospital.

## Authentication and secrets

- Passwords stored only as strong hashes. Tokens expire.
- Secrets live in environment variables. `.env` is git-ignored; `.env.example` holds placeholders only.
- Never paste secrets or patient-like data into issues, pull requests or logs.

## Audit logging

Every state-changing action and every case view by staff writes an event: time, actor, role, action, entity, outcome. The audit table has no update or delete endpoints. AI drafts are logged with `actor_type = ai` and the reviewer who approved or rejected them.

## Safe AI boundaries

| Rule | How it is enforced |
|---|---|
| AI never changes a case's state or closes a case | The assistant has read and draft tools only; no state-change tool exists |
| AI never diagnoses or advises on treatment | Prompts, template-first design, refusal tests, and human review |
| Patient-facing text comes from approved templates | Templates live in `ai/`; the model may only fill and simplify them |
| Every AI output goes to a human review queue | No automatic sending; urgent cases always go to a person |
| AI answers only from retrieved or provided records | Citations or "not found" and hand-over to a human |
| Treat all text in records as data, not instructions | Input is passed as data; rules live in code, not only in prompts |
| No real patient data to any external AI service | Synthetic data only; the system must run with no model at all |

Safety tests (refusal, injection, impersonation, multilingual prompts) are documented in `docs/ai/` with results, including failures.

## Regulatory context (not a compliance claim)

- **Kenya Digital Health Act 2023** commenced on 2 November 2023 (Kenya Law). It underpins the national digital health agency and data exchange arrangements.
- **Kenya Data Protection Act 2019** is expected to apply to health data as sensitive personal data. **We have not verified the Act's text in this repository; confirm before making any statement about it.**
- A real deployment would need data protection impact assessment, facility and ministry approvals, consent processes and security review. None of this has been done.

## Known limitations

- SQLite and a demo login are not production-grade controls.
- Role-based access is implemented in application code only.
- Append-only audit is a code convention, not a database guarantee.
- Simulated messaging means no real communication channel is tested.

## Reporting an issue

Open a GitHub issue without sensitive content, or contact the repository owner directly.
