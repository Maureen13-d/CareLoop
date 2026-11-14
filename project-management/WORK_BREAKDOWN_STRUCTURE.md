# Work Breakdown Structure

Tasks are grouped by workstream, not by person. Anyone can take any task: assign yourself on the GitHub issue. Priorities: **P0** needed for the demo, **P1** important, **P2** stretch. Milestones are defined in [MILESTONES.md](MILESTONES.md) and task order in [DEPENDENCIES.md](DEPENDENCIES.md).

## WS-PLAT: platform (`ws:platform`)

| ID | Task | Deliverable | Priority | Milestone |
|---|---|---|---|---|
| P1 | Scaffold repository: backend and frontend skeletons, `.env.example`, `.gitignore` additions | Project runs "hello world" end to end | P0 | M1 |
| P2 | Quickstart in README that works on a clean machine, no API keys | README run steps | P0 | M4 |
| P3 | Automated tests on pull requests (CI) | `.github/workflows/ci.yml` | P1 | M3 |
| P4 | Optional Docker Compose start | `docker-compose.yml` | P2 | M4 |

## WS-ENGINE: case engine (`ws:case-engine`)

| ID | Task | Deliverable | Priority | Milestone |
|---|---|---|---|---|
| E1 | Pathway YAML format and `cervical_cancer.yaml` (deadlines marked assumed) | `pathways/` files | P0 | M1 |
| E2 | Case state machine with allowed transitions and the evidence-to-close rule | `modules/pathways` + tests | P0 | M2 |
| E3 | Deadline checker, escalation rules and demo clock | Scheduled job + tests | P0 | M2 |
| E4 | Audit module (append-only) called by every state change | `modules/audit` | P0 | M2 |
| E5 | Authentication and role-based permission checks | `modules/auth` + tests | P0 | M2 |

## WS-REC: records and referrals (`ws:records-referrals`)

| ID | Task | Deliverable | Priority | Milestone |
|---|---|---|---|---|
| R1 | Models and migrations: users, departments, patients, consents, screenings, cases | Database schema | P0 | M1 |
| R2 | Referrals module with accept, reject and complete | `modules/referrals` | P0 | M2 |
| R3 | Tasks and appointments, including missed appointments | `modules/tasks` | P0 | M2 |
| R4 | Notifications: draft, review, simulated outbox, acknowledgement | `modules/notifications` | P0 | M3 |
| R5 | Analytics endpoints for the dashboard | `modules/analytics` | P1 | M3 |

## WS-FE: frontend (`ws:frontend`)

| ID | Task | Deliverable | Priority | Milestone |
|---|---|---|---|---|
| F1 | App shell, login, role-aware navigation | Frontend skeleton | P0 | M2 |
| F2 | Coordinator worklist: overdue, stuck, unowned | Worklist page | P0 | M2 |
| F3 | Case timeline and actions | Case page | P0 | M2 |
| F4 | Review queue for drafts and escalations | Review page | P0 | M3 |
| F5 | Metrics dashboard | Metrics page | P1 | M3 |
| F6 | Simulated patient acknowledgement view | Demo page | P1 | M3 |

## WS-DATA: data and AI (`ws:data-ai`)

| ID | Task | Deliverable | Priority | Milestone |
|---|---|---|---|---|
| D1 | Synthetic data generator and seed loader (all records labelled synthetic) | `database/seeds/` | P0 | M1 |
| D2 | Before/after simulation, repeated runs, mean and standard deviation, assumptions listed | Results table + notebook or script | P1 | M3 |
| D3 | Rule-based risk score with visible factors | `modules/risk` | P1 | M3 |
| D4 | Approved message templates (English; Kiswahili reviewed by a fluent speaker) | `ai/templates/` | P0 | M3 |
| D5 | Draft-only assistant, tool list and refusal and injection test set | `modules/assistant`, `ai/` tests | P2 | stretch |
| D6 | Offline trained-model experiment with proper validation | `ml/` | P2 | stretch |

## WS-DOCS: documentation and governance (`ws:docs-governance`)

| ID | Task | Deliverable | Priority | Milestone |
|---|---|---|---|---|
| G1 | Keep the documentation set consistent with the code | `docs/` | P0 | ongoing |
| G2 | Source the pathway stages and deadlines from the national guideline | Updated pathway doc | P0 | M1 |
| G3 | Role matrix, consent flow and AI boundaries written up with test evidence | `docs/security/`, `docs/ai/` | P0 | M3 |
| G4 | Text description, demo script and pitch | `docs/demo/` | P0 | M3 |
| G5 | Demo video under 3 minutes, public on YouTube, no third-party music or trademarks | Video link | P0 | M4 |
| G6 | Fresh-machine README test, licence and secrets check | Checklist done | P0 | M4 |
| G7 | Optional FHIR mapping and simulated export | `modules/interop`, `integrations/` | P2 | stretch |

## If time runs short, cut in this order

1. P4 Docker, G7 FHIR export, D6 model experiment
2. D5 AI assistant (templates only)
3. D2 simulation polish (keep one clean table)
4. F5 and F6 polish

Never cut: E2 to E5, R1 to R4, F2 to F4, D1, D4, G3, G5, G6.
