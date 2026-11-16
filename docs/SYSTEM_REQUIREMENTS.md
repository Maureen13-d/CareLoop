# System Requirements

Priorities: **P0** required for the demo, **P1** important, **P2** stretch. IDs are used in issues and pull requests.

## Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | Register synthetic patients using a pseudonymous reference | P0 |
| FR-02 | A screener records a concerning finding (not a diagnosis); with the person's permission this opens a navigation case | P0 |
| FR-03 | Define the care pathway in configuration (stages, owners, deadlines, escalation) | P0 |
| FR-04 | Move a case through stages; reject invalid transitions | P0 |
| FR-05 | Assign an owner and deadline at every stage | P0 |
| FR-06 | Detect late or missed steps (unconfirmed reminder, undelivered SMS, missed appointment, stalled journey) on a schedule and create navigator tasks | P0 |
| FR-07 | Close a case only with a hospital milestone showing care started, or a recorded human decision with a reason | P0 |
| FR-09 | Create appointment requests and navigator tasks, including for missed appointments | P0 |
| FR-10 | Send reminders from approved templates; no text or USSD screen contains a result, diagnosis or sensitive wording | P0 |
| FR-11 | Simulate USSD and SMS through a channel simulator, with reply codes 1 (confirm), 2 (change), 3 (help) and STOP | P0 |
| FR-12 | Navigator dashboard showing open tasks, stalled cases and the pathway funnel | P0 |
| FR-13 | Case timeline showing every event and owner | P0 |
| FR-14 | Navigator task queue showing confirmed barriers and a suggested next step | P0 |
| FR-15 | Role-based access control | P0 |
| FR-16 | Purpose-specific, revocable consent (invitation, SMS contact, sharing barriers with a navigator) | P0 |
| FR-17 | Audit log of every state change, access to a case, and assistant handoff to a human | P0 |
| FR-18 | Metrics: pathway funnel, time between stages, missed appointments, opt-outs, open tasks | P1 |
| FR-19 | Synthetic data generator and seed loader | P0 |
| FR-20 | Evaluation sets with written-up results: Lite mode precision and recall, crisis-detection recall, USSD and SMS length limits | P1 |
| FR-23 | Exchange FHIR R4 resources with a mock hospital process (appointment request out, milestones in); labelled simulated | P0 |
| FR-24 | Safety rules run before any other assistant step: crisis language and requests for a diagnosis produce a human handoff | P0 |
| FR-25 | Lite mode: menus plus keyword and phrase matching to approved messages, with no model | P0 |
| FR-26 | Barrier detection (fear, cost, transport, stigma, not knowing where to go); only barriers the person confirms reach a navigator | P0 |
| FR-27 | Knowledge base of approved passages, each with a source and review status; grounded retrieval shows the source or says it was not found | P0 |
| FR-28 | Small synthetic facility directory used to suggest where to go | P1 |
| FR-29 | Handoff and loop closure: arrival confirmed, hospital milestones watched, case closes when care has started | P0 |
| FR-30 | A person can opt out at any point; the choice is recorded and respected, and STOP is honoured immediately | P0 |
| FR-31 | Patient web view with chat and journey | P1 |

## Non-functional requirements

| ID | Requirement | Priority |
|---|---|---|
| NFR-01 | Runs on a clean machine from README steps, with no API keys required | P0 |
| NFR-02 | Works without any language model: safety rules, Lite mode and retrieval need no model or external call | P0 |
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
| NFR-13 | SMS and USSD text stays within channel length limits and never contains sensitive wording | P0 |

## Users (roles are permissions, not people)

- **Patient:** chats on the web or uses the simulated USSD and SMS channels; no staff login.
- **Navigator:** works the task list, calls people, explains costs, helps with transport, finds a clinic. Sees only barriers the person confirmed.
- **Counsellor:** takes over when the assistant hands off a distressed person.
- **Clinician:** confirms arrival and records hospital milestones in the demo.
- **Program manager:** sees aggregate metrics and audit summaries.
- **Admin:** manages users and configuration in the demo.

## Assumptions to revisit

- Stage deadlines in the demo pathway are placeholders until sourced from a national guideline (see [pathways/cervical-cancer.md](pathways/cervical-cancer.md)).
- Role names and permissions are a design choice for the demo, not a statement about any hospital's real structure.
