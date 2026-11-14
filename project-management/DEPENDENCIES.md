# Task Dependencies

"Depends on" means the task cannot be finished (and often not started) until the other task is merged. IDs match [WORK_BREAKDOWN_STRUCTURE.md](WORK_BREAKDOWN_STRUCTURE.md).

| Task | Depends on | Why |
|---|---|---|
| P1 Scaffold | none | Everyone needs a running skeleton |
| E1 Pathway YAML | G2 (draft) | Stages and deadlines come from the pathway doc |
| R1 Models and migrations | P1 | Needs the backend skeleton |
| D1 Synthetic data | R1 | Fills the tables R1 defines |
| E5 Auth | R1 (users table) | Needs users and roles |
| E4 Audit | R1, E5 | Needs the actor identity |
| E2 State machine | E1, R1, E4 | Reads the pathway, writes cases, logs events |
| E3 Deadline checker | E2 | Needs cases and deadlines |
| R2 Referrals | E2 | Moves cases through referral stages |
| R3 Tasks and appointments | E2 | Linked to cases |
| R4 Notifications | E2, D4 | Needs cases and approved templates |
| R5 Analytics | E2, D1 | Needs events and data to count |
| D4 Templates | G2 | Wording must follow the pathway stages |
| D2 Simulation | E2, E3, D1 | Same rules as the engine |
| D3 Risk score | D1, R3 | Uses appointment and delay history |
| F1 Shell and login | P1, E5 | Needs login endpoint |
| F2 Worklist | F1, E2 (API contract) | Needs the cases endpoint |
| F3 Case timeline | F1, E2 | Needs timeline endpoint |
| F4 Review queue | F1, R4, E3 | Needs drafts and escalations |
| F5 Metrics | F1, R5 | Needs analytics endpoints |
| F6 Patient acknowledgement | R4 | Needs notifications |
| G3 Governance evidence | E5, E4, R4 | Tests real behaviour |
| G4 Demo script | M2 working flow | Script must match the working demo |
| G5 Video | G4, M3 | Needs a stable build |
| G6 Fresh-machine test | P2, all P0 tasks | Final check |

## Critical path

`G2 pathway draft -> E1 -> E2 -> E3 -> R4/F4 -> G4 -> G5 -> submit`

Anything that blocks E2 blocks most of the project, so it is the first priority after the skeleton.

## Contracts to agree first (before parallel work)

1. The case state names and transition rules (see the cervical pathway doc).
2. The API shapes in `docs/API_DOCUMENTATION.md` for cases, transitions, notifications and escalations.
3. The database tables in `docs/DATABASE_DESIGN.md`.

Frontend and backend can then build in parallel against these.
