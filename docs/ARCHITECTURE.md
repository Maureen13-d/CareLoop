# Architecture

Status: design. Nothing here is implemented until the code and tests exist.

## Principles

1. **Complement, don't replace.** CareLoop sits above existing hospital systems and tracks cases across them.
2. **Modular monolith.** One backend program, one deployment, split into modules with clear boundaries. No microservices.
3. **Rules in code, AI as helper.** Case state, deadlines, escalation and closure are deterministic. AI drafts text for humans to approve.
4. **Pathways are data.** Stages, owners and deadlines are defined in `pathways/*.yaml`, so new pathways are configuration.
5. **Synthetic data only, privacy by design.** See [SECURITY_AND_PRIVACY.md](SECURITY_AND_PRIVACY.md).

## Overview

```mermaid
flowchart LR
  U[Staff browser] --> FE[Next.js frontend]
  FE -->|REST /api/v1| API[FastAPI backend]
  subgraph Backend modules
    API --> AUTH[auth]
    API --> PAT[patients]
    API --> SCR[screenings]
    API --> PW[pathways engine]
    API --> REF[referrals]
    API --> TSK[tasks and appointments]
    API --> NOT[notifications]
    API --> AUD[audit]
    API --> ANA[analytics]
    API --> RSK[risk]
    API --> AST[assistant]
    API --> INT[interop]
  end
  PW -->|reads| YAML[pathways/*.yaml]
  Backend modules --> DB[(SQLite by default)]
  SCHED[Deadline checker] --> PW
  AST --> TPL[ai/ templates and prompts]
  RSK -.-> ML[ml/ offline model file]
  INT -.-> FHIR[integrations/ sample FHIR, simulated]
```

Solid arrows are MVP. Dotted arrows are stretch goals.

## Backend modules

Each module has `router.py` (endpoints), `service.py` (rules), `models.py` (tables), `schemas.py` (data shapes) and tests.

| Module | Responsibility | MVP |
|---|---|---|
| `auth` | Login, roles, permission checks | Yes |
| `patients` | Pseudonymous patient records, consent records | Yes |
| `screenings` | Screening and assessment results; a positive result opens a case | Yes |
| `pathways` | Orchestration engine: case state machine, owners, deadlines, escalation, evidence-based closure | Yes |
| `referrals` | Referral between departments and its status | Yes |
| `tasks` | Tasks, appointments, follow-up tracking | Yes |
| `audit` | Append-only record of who did what and when | Yes |
| `notifications` | Message drafts, review, simulated outbox, acknowledgement | MVP-lite |
| `analytics` | Dashboard metrics | MVP-lite |
| `risk` | Missed-care-activity risk score (rule-based first) | MVP-lite |
| `assistant` | Draft-only AI helper with controlled tools | Stretch |
| `interop` | Mapping between CareLoop records and FHIR resources | Stretch |

**Boundary rules**
- A module reads and writes only its own tables. To use another module's data, call that module's service functions.
- Every state-changing action writes an audit event through the `audit` service.
- The frontend talks to the backend API only, never to the database.

## Key flow: a case from screening to closure

1. A positive screening result is recorded (`screenings`), which asks `pathways` to open a case with the stage owner and deadline taken from the pathway YAML.
2. A patient message is drafted (`notifications`), reviewed by staff, then sent to the simulated outbox.
3. Staff advance the case through the stages. Each transition is checked against allowed moves and recorded.
4. The deadline checker runs on a schedule (in-process), finds overdue cases and creates escalations visible in the review queue.
5. A case closes only when evidence is attached or an authorised person records a decision.

## Demo clock

Real deadlines span days. The deadline checker uses a configurable clock so the demo can show an escalation in seconds. The demo clock is a clearly labelled setting, not a hidden shortcut.

## Deployment

- **Default:** Python and Node installed locally, SQLite file created on first run.
- **Optional:** Docker Compose for one-command start.
- **Later:** PostgreSQL by changing `DATABASE_URL`; cloud hosting notes in `infrastructure/` when needed.

## Out of scope for the MVP

Real patient data, live integration with any hospital system or national exchange, real SMS or email delivery, clinical validation, diagnosis or treatment advice.
