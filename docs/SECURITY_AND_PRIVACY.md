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

| Capability | Navigator | Counsellor | Clinician | Program manager | Admin |
|---|---|---|---|---|---|
| View task list and case detail | Yes (confirmed barriers only) | Handed-off cases only | Yes | Aggregates only | No |
| Move case between non-clinical stages | Yes | No | Yes | No | No |
| Record arrival or hospital milestone | No | No | Yes | No | No |
| Close without evidence (human decision, reason required) | Yes | No | Yes | No | No |
| Read confidential conversations | No | Yes, after handoff | No | No | No |
| Take over a handoff from the assistant | Yes | Yes | No | No | No |
| View metrics | Yes | No | Limited | Yes | Yes |
| View audit log | No | No | No | Yes | Yes |
| Manage users and demo settings | No | No | No | No | Yes |

The patient has no staff login. Patients use the web chat or the simulated USSD and SMS channels.

The exact stage permissions will be fixed in the pathway configuration. This matrix is a design choice for the demo, not a description of any real hospital.

## Authentication and secrets

- Passwords stored only as strong hashes. Tokens expire.
- Secrets live in environment variables. `.env` is git-ignored; `.env.example` holds placeholders only.
- Never paste secrets or patient-like data into issues, pull requests or logs.

## Privacy for messages

- No result, diagnosis or sensitive wording appears in any SMS or USSD screen, because phones are often shared.
- Reminders show only a time and place, with reply codes 1 (confirm), 2 (change), 3 (help) and STOP.
- STOP and "I do not want to continue" are honoured immediately and recorded.
- Confidential conversations are stored apart from case tables. Only what the person agrees to share reaches a navigator.

## Audit logging

Every state-changing action and every case view by staff writes an event: time, actor, role, action, entity, outcome. The audit table has no update or delete endpoints. Assistant actions, including handoffs to a human, are logged with `actor_type = ai` and the person who took over.

## Safe AI boundaries

| Rule | How it is enforced |
|---|---|
| AI never changes a case's state or closes a case | The assistant has no state-change tool; people and the rules engine make those decisions |
| AI never diagnoses, recommends treatment or discourages assessment | Safety rules run first, approved content only, refusal tests |
| Distress or alarming text stops the assistant | Safety rules hand over to a human and log the handoff |
| Patient-facing text comes from approved content | Templates, lexicons and knowledge passages live in `ai/` with source and review status |
| Answers come only from the approved knowledge base | The reply shows its source, or says it was not found and offers a human |
| Text typed by a person is data, not instructions | Input is matched and retrieved against; rules live in code, not only in prompts |
| The system works with no model | Safety rules, Lite mode and retrieval need no model; a model is optional and web chat only |
| No real patient data to any external AI service | Synthetic data only |

The old rule that every AI output goes to a human review queue no longer applies to patient chat, because replies cannot wait for staff. The controls above replace it. Safety tests (refusal, injection, impersonation, crisis wording) are documented in `docs/ai/` with results, including failures.

## Regulatory context (not a compliance claim)

- **Kenya Digital Health Act 2023** commenced on 2 November 2023 (Kenya Law). It underpins the national digital health agency and data exchange arrangements.
- **Kenya Data Protection Act 2019** is expected to apply to health data as sensitive personal data. **We have not verified the Act's text in this repository; confirm before making any statement about it.**
- A real deployment would need data protection impact assessment, facility and ministry approvals, consent processes and security review. None of this has been done.

## Known limitations

- SQLite and a demo login are not production-grade controls.
- Role-based access is implemented in application code only.
- Append-only audit is a code convention, not a database guarantee.
- Simulated USSD and SMS mean no real communication channel is tested, and shared-phone risks are handled by wording rules only.

## Reporting an issue

Open a GitHub issue without sensitive content, or contact the repository owner directly.
