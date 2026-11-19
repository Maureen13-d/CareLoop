# Task Dependencies

"Depends on" means the task cannot be finished (and often not started) until the other task is merged. IDs match [WORK_BREAKDOWN_STRUCTURE.md](WORK_BREAKDOWN_STRUCTURE.md).

| Task | Depends on | Why |
|---|---|---|
| P1 Scaffold | none | Backend skeleton exists on the branch; frontend skeleton still needed |
| E1 Pathway YAML | pathway doc merged, backend branch merged | The loader and tests live on `feature/backend-case-engine` |
| E3 Models | backend branch merged | Models already exist; adapt them |
| D1 Synthetic data | E3 | Fills the tables E3 defines |
| E5 Auth | E3 | Needs users and roles |
| E4 Audit | E3, E5 | Needs the actor identity |
| E2 State machine | E1, E3, E4 | Reads the pathway, writes cases, logs events |
| E6 Deadline checker | E2 | Needs cases and deadlines |
| A1 Safety rules | P1 | Pure rules, can start early |
| A3 Knowledge base | P1 | Content work, can start early |
| A2 Lite mode | A1, E3 | Runs after safety rules and writes barrier flags |
| A4 Grounded retrieval | A1, A3 | Needs the passages and the safety step |
| A5 Barrier confirmation and tasks | A2, E2, E6 | Creates navigator tasks on cases |
| C1 Channels and simulator | P1, E3 | Adapters need the patient and session tables |
| C2 SMS outbox | C1, E2 | Needs channel layer and case state |
| C3 Appointments and reminders | C2, E2 | Needs templates and cases |
| C4 Missed-step detection | C3, E6 | Needs reminders and the deadline checker |
| I1 FHIR adapter | E3 | Maps CareLoop records |
| I2 Mock hospital | I1 | Needs the message shapes |
| I3 Handoff and closure | I2, C3, E2 | Needs appointments, the mock hospital and the state machine |
| F1 Shell and login | P1, E5 | Needs the login endpoint |
| F2 Dashboard | F1, A5, E6 | Needs tasks and the funnel data |
| F3 Case timeline | F1, E2 | Needs the timeline endpoint |
| F4 Patient web view | F1, A4 | Needs the assistant endpoint |
| D2 Evaluation | A1, A2, C2 | Tests the real rules and templates |
| D3 Safety tests | A1, A2, A4 | Tests real behaviour |
| G3 Governance evidence | E5, E4, A1, C2 | Tests real behaviour |
| G4 Demo script | M2 working flow | Script must match the working demo |
| G5 Video | G4, M3 | Needs a stable build |
| G6 Fresh-machine test | P2, all P0 tasks | Final check |

## Critical path

`pathway files -> E1 -> E2 -> E6 -> A5 and C3 -> I3 -> G4 -> G5 -> submit`

Anything that blocks E2 blocks most of the project, so it is the first priority. Step zero: merge `main` into `feature/backend-case-engine`, resolve conflicts, and open a pull request so the existing engine reaches `main`. A1 and A3 can start on day one because they do not depend on the engine.

## Contracts to agree first (before parallel work)

1. The case state names and transition rules (see the pathway doc and `pathways/cervical_cancer.yaml`).
2. The API shapes in `docs/API_DOCUMENTATION.md`.
3. The database tables in `docs/DATABASE_DESIGN.md`.

Frontend and backend can then build in parallel against these.
