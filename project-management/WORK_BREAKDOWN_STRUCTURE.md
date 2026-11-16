# Work Breakdown Structure

Tasks are grouped by workstream, not by person. Anyone can take any task: assign yourself on the GitHub issue. Priorities: **P0** needed for the demo, **P1** important, **P2** stretch. Milestones are defined in [MILESTONES.md](MILESTONES.md) and task order in [DEPENDENCIES.md](DEPENDENCIES.md). Aligned with the README phases on 2026-11-16.

**Existing code.** The branch `feature/backend-case-engine` already has auth and roles, audit, patients and consents, screenings, a YAML-driven state machine with deadlines, escalation and closure, a seed script and tests, built for the earlier hospital-side pathway. Treat E1 to E6 and D1 as *adapt*, not *build*, and merge that branch into `main` first.

## WS-PLAT: platform (`ws:platform`)

| ID | Task | Deliverable | Priority | Milestone |
|---|---|---|---|---|
| P1 | Scaffold: the backend skeleton exists on `feature/backend-case-engine`; still needed are the frontend skeleton, a health check page and run steps | Project runs "hello world" end to end | P0 | M1 |
| P2 | Quickstart in README that works on a clean machine, no API keys | README run steps | P0 | M4 |
| P3 | Automated tests on pull requests (CI) | `.github/workflows/ci.yml` | P1 | M3 |
| P4 | Optional Docker Compose start | `docker-compose.yml` | P2 | M4 |

## WS-ENGINE: case engine (`ws:case-engine`)

| ID | Task | Deliverable | Priority | Milestone |
|---|---|---|---|---|
| E1 | Adapt `pathways/cervical_cancer.yaml` to the new states, owners and roles (deadlines marked assumed); the existing loader stays | `pathways/` files | P0 | M1 |
| E2 | Adapt the existing state machine, role checks and evidence-to-close rule to the new pathway, and update its tests | `modules/pathways` + tests | P0 | M1 |
| E3 | Adapt models: roles, consent purposes, patient fields; add new tables as other workstreams need them | Database schema | P0 | M1 |
| E4 | Audit module: exists; extend it to log assistant handoffs and channel events | `modules/audit` | P0 | M1 |
| E5 | Auth and roles: exists; rename coordinator to navigator and add counsellor | `modules/auth` + tests | P0 | M1 |
| E6 | Adapt the existing deadline checker and escalations into navigator tasks; keep the demo clock | Scheduled job + tests | P0 | M2 |

## WS-ASSIST: assistant (`ws:assistant`)

| ID | Task | Deliverable | Priority | Milestone |
|---|---|---|---|---|
| A1 | Safety rules (crisis language, requests for a diagnosis) with human handoff | `modules/assistant`, `ai/safety` + tests | P0 | M2 |
| A2 | Lite mode: menus, keyword lexicon, barrier flags | `ai/lexicon`, `modules/barriers` | P0 | M2 |
| A3 | Knowledge base v1: 20 to 30 passages, each with source and review status | `ai/knowledge` | P0 | M2 |
| A4 | Grounded retrieval for web chat, with visible source | `modules/assistant` | P0 | M2 |
| A5 | Barrier confirmation and navigator task creation | `modules/barriers`, `modules/tasks` | P0 | M2 |
| A6 | Optional language-model mode for web chat behind a swappable interface | `modules/assistant` | P2 | stretch |
| A7 | Kiswahili Lite mode, reviewed by a fluent speaker | `ai/lexicon` | P2 | stretch |

## WS-CHAN: channels (`ws:channels`)

| ID | Task | Deliverable | Priority | Milestone |
|---|---|---|---|---|
| C1 | Channel layer, adapters and channel simulator (USSD screen and SMS inbox) | `modules/channels`, `integrations/channel_simulator` | P0 | M2 |
| C2 | SMS outbox with approved templates, reply codes and STOP | `modules/channels`, `ai/templates` | P0 | M2 |
| C3 | Appointment requests and reminders | `modules/appointments` | P0 | M2 |
| C4 | Missed-appointment and undelivered-SMS detection | `modules/appointments`, `modules/tasks` | P0 | M2 |

## WS-INTEROP: interoperability (`ws:interop`)

| ID | Task | Deliverable | Priority | Milestone |
|---|---|---|---|---|
| I1 | FHIR mapping and the adapter interface | `modules/interop` | P0 | M3 |
| I2 | Mock hospital system as a separate process | `integrations/mock_hospital` | P0 | M3 |
| I3 | Appointment request out, milestones in, handoff and loop closure | `modules/interop` + tests | P0 | M3 |

## WS-FE: frontend (`ws:frontend`)

| ID | Task | Deliverable | Priority | Milestone |
|---|---|---|---|---|
| F1 | App shell, login, role-aware navigation | Frontend skeleton | P0 | M1 |
| F2 | Navigator dashboard: task list and pathway funnel | Dashboard page | P0 | M3 |
| F3 | Case timeline and actions | Case page | P0 | M2 |
| F4 | Patient web view: chat and journey | Patient page | P1 | M3 |

## WS-DATA: data and evaluation (`ws:data-eval`)

| ID | Task | Deliverable | Priority | Milestone |
|---|---|---|---|---|
| D1 | Adapt the existing seed script (`database/seeds/seed_demo.py`) to the new pathway; all records labelled synthetic | `database/seeds/` | P0 | M1 |
| D2 | Evaluation sets and written-up results: Lite mode precision and recall, crisis-detection recall, USSD and SMS length limits | `ai/eval`, results doc | P0 | M3 |
| D3 | Safety and refusal tests documented, including failures | `docs/ai/` | P0 | M3 |

## WS-DOCS: documentation and governance (`ws:docs-governance`)

| ID | Task | Deliverable | Priority | Milestone |
|---|---|---|---|---|
| G1 | Keep the documentation set consistent with the code and the README Status table | `docs/` | P0 | ongoing |
| G2 | Source the pathway deadlines from the national guideline, or keep them labelled assumed | Updated pathway doc | P1 | M3 |
| G3 | Role matrix, consent flow and AI boundaries written up with test evidence | `docs/security/`, `docs/ai/` | P0 | M3 |
| G4 | Text description, demo script and pitch | `docs/demo/` | P0 | M3 |
| G5 | Demo video under 3 minutes, public on YouTube, no third-party music or trademarks | Video link | P0 | M4 |
| G6 | Fresh-machine README test, licence and secrets check, remove Team notes | Checklist done | P0 | M4 |
| G7 | Find a clinical reviewer for the knowledge base and safety wording; mark passages pending review until then | Reviewer named or status recorded | P0 | M2 |

## If time runs short, cut in this order

1. P4 Docker, A6 language model, A7 Kiswahili
2. F4 patient web view polish (keep a simple chat)
3. I1 to I3 reduced to one Appointment out and one milestone back
4. Dashboard polish (keep one funnel)

Never cut: E1 to E6, A1 to A3, C1 to C4, F2, F3, D1 to D3, G3, G5, G6.
