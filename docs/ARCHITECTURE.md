# Architecture

Status: design. Nothing here is implemented until the code and tests exist. Aligned with the README on 2026-11-16.

## Principles

1. **Complement, don't replace.** CareLoop sits before the hospital and watches a few coarse milestones after handoff. Hospital systems own diagnostics, referrals and treatment.
2. **Modular monolith.** One backend program, one deployment, split into modules with clear boundaries. No microservices. The mock hospital is a separate process only because it plays a different system.
3. **Rules in code, AI as helper.** Case state, deadlines and closure are deterministic. The assistant works in tiers and always falls back to the simpler one.
4. **Pathways are data.** Stages, owners and deadlines are defined in `pathways/*.yaml`, so new pathways are configuration.
5. **Channel-agnostic core.** The core and the assistant do not know which channel a message came from.
6. **Synthetic data only, privacy by design.** See [SECURITY_AND_PRIVACY.md](SECURITY_AND_PRIVACY.md).

## Overview

```mermaid
flowchart LR
  PH["Basic phone: USSD and SMS"] --> SIM[Channel simulator]
  WEB["Smartphone: web chat"] --> FE[Next.js frontend]
  NAV[Navigator browser] --> FE
  SIM -->|channel adapter| API
  FE -->|REST /api/v1| API[FastAPI backend]
  subgraph Backend modules
    API --> AUTH[auth]
    API --> PAT["patients and consent"]
    API --> FLG[screenings]
    API --> PW[pathways engine]
    API --> AST["assistant: safety, Lite, retrieval"]
    API --> BAR[barriers]
    API --> TSK[navigator tasks]
    API --> APT[appointments]
    API --> CH["channels: USSD and SMS"]
    API --> INT[interop: FHIR adapter]
    API --> AUD[audit]
    API --> ANA[analytics]
  end
  PW -->|reads| YAML[pathways/*.yaml]
  AST --> AI["ai/ knowledge base, lexicon, templates"]
  AST -.-> LLM[optional language model]
  INT -->|FHIR over HTTP, simulated| MOCK[Mock hospital process]
  Backend modules --> DB[(SQLite by default)]
  SCHED[Deadline checker] --> PW
```

Solid arrows are MVP. Dotted arrows are optional.

## Backend modules

Each module has `router.py` (endpoints), `service.py` (rules), `models.py` (tables), `schemas.py` (data shapes) and tests.

| Module | Responsibility | MVP |
|---|---|---|
| `auth` | Login, roles, permission checks | Yes |
| `patients` | Pseudonymous patient records, purpose-specific consent, opt-outs | Yes |
| `screenings` | Screening results recorded by a screener; a concerning finding with consent opens a case | Yes |
| `pathways` | Case state machine, owners, deadlines, evidence-based closure | Yes |
| `assistant` | Safety rules, Lite mode, grounded retrieval, optional model | Yes |
| `barriers` | Detected barriers, patient confirmation, sharing with a navigator | Yes |
| `tasks` | Navigator tasks created by the system or by people | Yes |
| `appointments` | Appointment requests, confirmation, reminders, missed visits | Yes |
| `channels` | USSD and SMS adapters, reply codes, STOP, simulated outbox | Yes |
| `interop` | FHIR mapping and the adapter to the mock hospital | Yes |
| `audit` | Append-only record of who did what and when | Yes |
| `analytics` | Pathway funnel and dashboard metrics | Yes |

**Boundary rules**
- A module reads and writes only its own tables. To use another module's data, call that module's service functions.
- Every state-changing action writes an audit event through the `audit` service.
- The frontend talks to the backend API only, never to the database.
- Confidential conversations are readable only through the `assistant` module's access-controlled service.

## Key flow: from finding to handoff

1. A screener records a concerning finding (`screenings`). With the person's permission it opens a case in `pathways`, with the owner and deadline from the pathway YAML.
2. The person joins on web chat, USSD or SMS. The assistant answers from approved content. Safety rules run first, and a crisis message hands over to a human.
3. Barriers are noticed, the person confirms them, and only confirmed barriers reach a navigator as a task.
4. The navigator helps with cost, transport or finding a clinic, then an appointment request goes to the clinic through `interop`.
5. The clinic confirms. A discreet reminder goes out by SMS with reply codes. An unconfirmed or undelivered reminder, or a missed appointment, creates a navigator task.
6. When arrival is confirmed, hospital systems take over. CareLoop watches a few milestones and closes the case when care has started, or a human decides otherwise.

## Demo clock

Real deadlines span days. The deadline checker uses a configurable clock so the demo can show a missed step in seconds. The demo clock is a clearly labelled setting, not a hidden shortcut.

## Deployment

- **Default:** Python and Node installed locally, SQLite file created on first run, no API key needed.
- **Optional:** Docker Compose for one-command start.
- **Later:** PostgreSQL by changing `DATABASE_URL`.

## Out of scope for the MVP

Real patient data, live integration with any hospital system or national exchange, a live short code or real messaging, hospital-internal tracking, predictive machine learning, clinical validation, diagnosis or treatment advice.
