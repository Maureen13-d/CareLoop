# System Requirements

Priorities: **P0** required for the demo, **P1** important, **P2** stretch. IDs are used in issues and pull requests.

## Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | Register synthetic patients using a pseudonymous reference | P0 |
| FR-02 | Record screening results; a positive or suspicious result opens a care case | P0 |
| FR-03 | Define the care pathway in configuration (stages, owners, deadlines, escalation) | P0 |
| FR-04 | Move a case through stages; reject invalid transitions | P0 |
| FR-05 | Assign an owner and deadline at every stage | P0 |
| FR-06 | Detect overdue cases on a schedule and create escalations | P0 |
| FR-07 | Close a case only with evidence or a recorded human decision | P0 |
| FR-08 | Create and track referrals (sent, accepted, rejected, completed) | P0 |
| FR-09 | Create tasks and appointments, including missed appointments | P0 |
| FR-10 | Draft patient messages from approved templates for staff review | P0 |
| FR-11 | Simulate message sending and patient acknowledgement | P0 |
| FR-12 | Coordinator dashboard showing overdue, stuck and unowned cases | P0 |
| FR-13 | Case timeline showing every event and owner | P0 |
| FR-14 | Human review queue for drafts and escalations | P0 |
| FR-15 | Role-based access control | P0 |
| FR-16 | Consent records per patient and purpose | P1 |
| FR-17 | Audit log of every state change, access to a case, and AI draft | P0 |
| FR-18 | Metrics: time to notification, confirmation, referral acceptance, treatment start; unresolved cases | P1 |
| FR-19 | Synthetic data generator and seed loader | P0 |
| FR-20 | Before/after simulation reported as mean and standard deviation over repeated runs | P1 |
| FR-21 | Rule-based risk score for likely missed next activity, with the contributing factors shown | P1 |
| FR-22 | AI assistant that drafts summaries and messages using read and draft tools only | P2 |
| FR-23 | Export sample records as FHIR resources, labelled simulated | P2 |

## Non-functional requirements

| ID | Requirement | Priority |
|---|---|---|
| NFR-01 | Runs on a clean machine from README steps, with no API keys required | P0 |
| NFR-02 | Works without any language model installed (template fallback) | P0 |
| NFR-03 | Synthetic data only; clearly labelled as such in the UI and repo | P0 |
| NFR-04 | Passwords hashed; secrets only in environment variables | P0 |
| NFR-05 | Every API response avoids unnecessary patient detail (data minimisation, role-based views) | P0 |
| NFR-06 | Audit events are append-only in application code | P0 |
| NFR-07 | Backend tests cover the state machine, closure rule and role access | P1 |
| NFR-08 | Typical dashboard and case pages respond in under 2 seconds on a laptop with demo data | P1 |
| NFR-09 | Timestamps stored in UTC (ISO 8601) | P1 |
| NFR-10 | Open-source licence (MIT) and public repository | P0 |
| NFR-11 | Message text supports English and Kiswahili templates; translations reviewed by a fluent speaker before demo use | P2 |
| NFR-12 | Code structured so SQLite can be replaced by PostgreSQL through configuration | P1 |

## Users (roles are permissions, not people)

- **Coordinator:** works the worklist, reviews drafts, handles escalations.
- **Clinician:** confirms results, accepts referrals, records evidence and decisions.
- **Program manager:** sees aggregate metrics and audit summaries.
- **Admin:** manages users and configuration in the demo.
- **Patient (simulated):** receives messages and acknowledges via a demo link; no patient login in the MVP.

## Assumptions to revisit

- Stage deadlines in the demo pathway are placeholders until sourced from a national guideline (see [pathways/cervical-cancer.md](pathways/cervical-cancer.md)).
- Role names and permissions are a design choice for the demo, not a statement about any hospital's real structure.
