

#!/usr/bin/env python3
"""
align_docs.py - aligns the CareLoop repo with the new README (pre-hospital navigation).

Run from the repo root, on a fresh branch:
    python3 align_docs.py

It edits files in memory first and writes to disk only if every edit matched,
so a failure changes nothing. It does not commit. Review with `git diff`.

Run it on a branch made from `main` (not on feature/backend-case-engine). It does not touch
the backend code, the pathway YAML or .env.example that live on that branch.
"""
import pathlib
import sys

ROOT = pathlib.Path.cwd()
ORIG = {}   # path -> original text (None for new files)
CACHE = {}  # path -> new text


def die(msg):
    print("ERROR:", msg)
    print("Nothing was changed.")
    sys.exit(1)


def read(path):
    if path in CACHE:
        return CACHE[path]
    f = ROOT / path
    if not f.exists():
        die(f"{path} not found. Run this from the CareLoop repo root.")
    ORIG[path] = f.read_text(encoding="utf-8")
    CACHE[path] = ORIG[path]
    return CACHE[path]


def write(path, text):
    if path not in CACHE:
        if (ROOT / path).exists():
            read(path)
        else:
            ORIG[path] = None
    CACHE[path] = text.strip("\n") + "\n"


def _find_line(path, prefix):
    lines = read(path).split("\n")
    idx = [i for i, l in enumerate(lines) if l.startswith(prefix)]
    if len(idx) != 1:
        die(f"{path}: expected exactly 1 line starting with {prefix!r}, found {len(idx)}")
    return lines, idx[0]


def sub_line(path, prefix, new):
    lines, i = _find_line(path, prefix)
    lines[i] = new.strip("\n")
    CACHE[path] = "\n".join(lines)


def drop_line(path, prefix):
    lines, i = _find_line(path, prefix)
    del lines[i]
    CACHE[path] = "\n".join(lines)


def insert_after_line(path, prefix, new):
    lines, i = _find_line(path, prefix)
    lines.insert(i + 1, new.strip("\n"))
    CACHE[path] = "\n".join(lines)


def edit_line(path, prefix, old, new):
    lines, i = _find_line(path, prefix)
    if old not in lines[i]:
        die(f"{path}: {old!r} not found in the line starting with {prefix!r}")
    lines[i] = lines[i].replace(old, new, 1)
    CACHE[path] = "\n".join(lines)


def replace_text(path, old, new):
    t = read(path)
    if t.count(old) != 1:
        die(f"{path}: expected exactly 1 occurrence of {old[:60]!r}, found {t.count(old)}")
    CACHE[path] = t.replace(old, new, 1)


def replace_between(path, start, end, new):
    """Replace from the line `start` up to (not including) `end`. end=None means to end of file."""
    t = read(path)
    i = t.find(start)
    if i < 0:
        die(f"{path}: start marker {start[:60]!r} not found")
    if end is None:
        CACHE[path] = t[:i] + new.strip("\n") + "\n"
        return
    j = t.find(end, i + len(start))
    if j < 0:
        die(f"{path}: end marker {end[:60]!r} not found")
    CACHE[path] = t[:i] + new.strip("\n") + "\n\n" + t[j:]


# --------------------------------------------------------------------------
# Guard: do not run twice
# --------------------------------------------------------------------------
if "TD-12" in read("docs/TECHNICAL_DECISIONS.md"):
    print("Already applied (TD-12 exists in docs/TECHNICAL_DECISIONS.md). Nothing to do.")
    sys.exit(0)

# --------------------------------------------------------------------------
# 1. docs/TECHNICAL_DECISIONS.md
# --------------------------------------------------------------------------
TD = "docs/TECHNICAL_DECISIONS.md"
edit_line(TD, "| TD-07 |", "| Accepted |", "| Superseded by TD-12 |")
edit_line(TD, "| TD-08 |", "| Accepted |", "| Superseded by TD-14 |")
edit_line(TD, "| TD-09 |", "| Accepted |", "| Superseded by TD-15 |")
insert_after_line(TD, "| TD-11 |", """
| TD-12 | Scope is pre-hospital patient navigation; hospital-internal tracking (departments, referrals, treatment) is out of scope | Accepted | 2026-11-16 |
| TD-13 | USSD and SMS are simulated behind channel adapters; no live short code or provider | Accepted | 2026-11-16 |
| TD-14 | Assistant works in tiers (safety rules, Lite mode, grounded retrieval, optional model) and runs with no model | Accepted | 2026-11-16 |
| TD-15 | Mock hospital runs as a separate process and exchanges FHIR R4 resources over HTTP; everything is simulated | Accepted | 2026-11-16 |
| TD-16 | Pre-hospital pathway states: FLAGGED to CLOSED, plus OPTED_OUT and LOST_TO_FOLLOW_UP | Accepted | 2026-11-16 |
| TD-17 | Adapt the existing backend case engine on `feature/backend-case-engine` to the new pathway instead of rebuilding it | Proposed | 2026-11-16 |
""")
write(TD, read(TD) + """
**TD-12 Pre-hospital scope.** The README defines CareLoop as the bridge between a concerning screening finding and professional assessment. Hospitals already own diagnostics, internal referrals and treatment, and we cannot verify or integrate with those systems, so tracking them would be out of reach and a claim we cannot back. This supersedes TD-07: predictive scoring is not planned, and barrier detection comes from Lite mode plus the person's own confirmation.

**TD-13 Simulated channels.** A real short code needs licensing through the Communications Authority and mobile networks, which we have not obtained. Channel adapters keep the core and the assistant unaware of which channel a message came from, so a real provider can replace the simulator later.

**TD-14 Tiered assistant.** This supersedes TD-08. Safety rules run first. Lite mode (menus, keywords, approved messages) needs no model. Retrieval shows its source. A language model is an optional extra for web chat only. Every tier falls back to the simpler one on failure. Patient chat cannot wait for staff to approve each reply, so safety comes from approved content, refusal rules and human handoff instead of a review queue.

**TD-15 Mock hospital.** This supersedes TD-09. A separate process lets us show a real HTTP exchange of FHIR R4 resources (appointment request out, milestones back) and reject invalid messages with a clear error. It is a simulation: no live integration with any hospital system, TaifaCare, KenyaEMR or the national exchange is claimed.

**TD-16 Pathway states.** The states follow the README's ten steps and replace the hospital-side stages. OPTED_OUT records a person's decision not to continue. LOST_TO_FOLLOW_UP can only be set by a human decision. All stage deadlines are assumptions until sourced.

**TD-17 Adapt, do not rebuild.** The branch `feature/backend-case-engine` already has authentication and roles, an append-only audit log, patients and consents, screenings, a YAML-driven state machine with deadlines, escalation, closure with evidence and a human lost-to-follow-up decision, a seed script and tests. It was built for the earlier hospital-side pathway. Because stages, owners, roles and closure rules are read from `pathways/*.yaml`, most of the work is a new pathway file, renamed roles and updated tests. Status stays Proposed until the team agrees.
""")

# --------------------------------------------------------------------------
# 2. docs/pathways/cervical-cancer.md
# --------------------------------------------------------------------------
write("docs/pathways/cervical-cancer.md", """
# Demo Pathway: Cervical Cancer Screening-to-Care Navigation (Kenya context)

Status: **draft**. This is the pre-hospital navigation pathway. It starts when a screener records a concerning finding and ends when the hospital's own systems have taken over and care has started. **No deadline below has been sourced from a national guideline.** All deadlines are placeholders marked ASSUMED, to be replaced with guideline-sourced values or kept and labelled as assumptions.

## Scope

In scope: a person with a concerning screening finding, from invitation to CareLoop through support, barrier detection, navigation, appointment request and reminders, arrival confirmation, handoff, and a light check that care started.

Out of scope: diagnosis, treatment decisions, referrals between hospital departments, departmental tasks, clinical follow-up, screening invitation and recall, vaccination. After handoff CareLoop only watches a few coarse milestones.

## Stages

| # | State | Meaning | Owner | Deadline to leave stage (ASSUMED) |
|---|---|---|---|---|
| 1 | `FLAGGED` | Screener recorded a concerning finding (not a diagnosis) | Screener | Person invited, with permission, within 2 days |
| 2 | `ENGAGED` | Person joined on web chat, USSD or SMS | System (assistant) | Barriers asked about within 3 days |
| 3 | `BARRIERS_ASSESSED` | Barriers confirmed by the person; only confirmed ones reach a navigator | System, then navigator | Navigator contact within 2 days |
| 4 | `NAVIGATION` | Navigator helping with cost, transport or finding a clinic | Navigator | Appointment requested within 7 days |
| 5 | `APPOINTMENT_BOOKED` | Clinic confirmed the request; discreet reminder sent | Clinic, navigator watching | Arrival within 14 days |
| 6 | `ARRIVAL_CONFIRMED` | Clinic confirmed the person arrived | Clinic | Handoff recorded within 1 day |
| 7 | `HANDED_OFF` | Hospital systems and staff own all clinical care; CareLoop watches milestones | Hospital | Milestone received within 21 days |
| 8 | `CLOSED` | Closed with evidence | n/a | n/a |
| 9 | `OPTED_OUT` | Person chose not to continue; recorded and respected | n/a | n/a |
| 10 | `LOST_TO_FOLLOW_UP` | Closed by a human decision after navigator attempts | n/a | n/a |

A person can move to `OPTED_OUT` from any stage. A missed appointment moves the case from `APPOINTMENT_BOOKED` back to `NAVIGATION` with a task. It is treated as a problem to solve, not a failure by the patient.

## Events and what happens

| Event | Automatic | Human step |
|---|---|---|
| Reminder not confirmed in time | Navigator task | Navigator calls the person |
| SMS undelivered | Navigator task | Navigator finds another way to reach the person |
| Appointment missed | Case returns to `NAVIGATION`, task created | Navigator finds out why and helps rebook |
| Stage deadline passed | Navigator task | Navigator checks in |
| No hospital milestone for too long | Check-in task | Navigator checks that the person is not lost |
| Crisis or alarming text | Assistant stops and hands over | Counsellor or navigator takes over |
| STOP or "I do not want to continue" | Messages stop, state `OPTED_OUT` | None; the choice is respected |

Automatic: reminders, noticing late or missed steps, creating tasks, recording every step. Always a human: clinical decisions, handling distress, deciding someone is lost to follow-up, closing a case without evidence.

## Closure evidence

`CLOSED` requires one of: a hospital milestone showing care started, or a recorded decision by an authorised person with a reason. `LOST_TO_FOLLOW_UP` is only ever a recorded human decision.

## Needs sourcing before the demo

- Real stage windows from the national guideline, or keep the assumptions labelled.
- Which hospital milestones are realistic to receive (the demo uses `assessment_completed` and `care_started`).
- A clinical reviewer for the safety wording and the knowledge base.
- Helpline information to verify. Do not put a number in the repository until it has been checked.

The same data will live in `pathways/cervical_cancer.yaml`, so the engine reads it from configuration. The file on the `feature/backend-case-engine` branch is the earlier hospital-side version and is replaced when the engine is adapted.
""")


# --------------------------------------------------------------------------
# 3. docs/DATABASE_DESIGN.md
# --------------------------------------------------------------------------
write("docs/DATABASE_DESIGN.md", """
# Database Design

Status: design. SQLite by default through SQLAlchemy, migrations through Alembic. Names are proposals and will be refined during implementation. Aligned with the README on 2026-11-16 (pre-hospital navigation).

## Conventions

- Primary keys: integer `id`. Foreign keys enforced (`PRAGMA foreign_keys=ON`).
- Timestamps: UTC, ISO 8601.
- JSON fields are stored as text in SQLite.
- Patients are identified by a pseudonymous `patient_ref` (for example `CL-000123`). All demo data is synthetic.
- Audit and case-event tables are append-only in application code (no update or delete endpoints).
- Each table belongs to one backend module; other modules use that module's service functions.
- Tables marked "Exists in code" are already implemented on `feature/backend-case-engine`; adapt them instead of recreating them.
- Confidential conversation tables are separate from case tables and readable only by the roles that need them.
- Nothing stored for an SMS or USSD screen contains a result, diagnosis or sensitive wording.

## Entity relationships

```mermaid
erDiagram
  users ||--o{ audit_log : acts
  patients ||--o{ consents : gives
  patients ||--o{ screenings : has
  patients ||--o{ care_cases : has
  patients ||--o{ conversations : holds
  patients ||--o{ ussd_sessions : opens
  patients ||--o{ opt_outs : records
  screenings ||--o| care_cases : opens
  care_cases ||--o{ case_events : records
  care_cases ||--o{ barrier_flags : has
  care_cases ||--o{ navigator_tasks : has
  care_cases ||--o{ appointments : has
  care_cases ||--o{ sms_messages : sends
  care_cases ||--o{ evidence : holds
  conversations ||--o{ messages : contains
  facilities ||--o{ appointments : hosts
  departments ||--o{ care_cases : owns
```

## Tables

| Table | Module | Key columns | Notes |
|---|---|---|---|
| `users` | auth | username, password_hash, role, display_name, department_id, active | Exists in code. Roles: navigator (renamed from coordinator), counsellor (new), clinician, program_manager, admin |
| `departments` | auth | name, label, type | Exists in code. Owner groups for pathway stages, for example screening, navigation, clinic |
| `facilities` | facilities | name, type, zone (synthetic), accepts_appointments | Small synthetic directory |
| `patients` | patients | patient_ref, display_name (synthetic), age_band, zone (synthetic), preferred_language, is_synthetic, contact_ref (synthetic), channel_preference | Exists in code. No real identifiers. `contact_ref` and `channel_preference` are new |
| `consents` | patients | patient_id, purpose, granted, granted_at, revoked_at | Exists in code. New purposes: invitation, sms_contact, share_barriers_with_navigator (replacing care_coordination, sms_reminders, data_sharing_between_facilities). Purpose-specific and revocable |
| `opt_outs` | patients | patient_id, scope, recorded_at | Scope: sms_stop or leave_programme. Honoured immediately |
| `screenings` | screenings | patient_id, screening_type, result, performed_at, department_id, recorded_by, invited_with_consent | Exists in code. A concerning finding, not a diagnosis. `invited_with_consent` is new |
| `care_cases` | pathways | patient_id, source_screening_id, pathway_id, pathway_version, state, urgency, owner_user_id, owner_department_id, state_entered_at, deadline_at, opened_at, closed_at, closure_reason | Exists in code. One row per tracked case |
| `case_events` | pathways | case_id, from_state, to_state, actor_id, actor_type (user/system/ai), occurred_at, note | Exists in code. Append-only timeline |
| `evidence` | pathways | case_id, type, description, reference, recorded_by, recorded_at | Exists in code. Required to close a case. Hospital milestones from the mock hospital are stored here |
| `barrier_flags` | barriers | case_id, barrier_type, source, detected_at, confirmed_by_patient, confirmed_at, shared_with_navigator | Types: fear, cost, transport, stigma, not_knowing_where. Source: lite_text, menu, navigator. Only confirmed flags are visible to a navigator |
| `navigator_tasks` | tasks | case_id, task_type, reason, assigned_user_id, due_at, status, completed_at, created_by | Replaces the existing `escalations` table; start from that model. Created by the system or a navigator. Types: barrier, unconfirmed_reminder, undelivered_sms, missed_appointment, stalled, milestone_check |
| `appointments` | appointments | case_id, patient_id, facility_id, requested_at, scheduled_at, status, reminder_status | Status: requested, confirmed, attended, missed, cancelled |
| `sms_messages` | channels | case_id, patient_id, direction, template_id, body, status, reply_code, created_at, delivered_at | Status: queued, delivered, undelivered, replied. Reply codes 1, 2, 3, STOP |
| `ussd_sessions` | channels | session_ref, patient_id, current_menu, started_at, ended_at | Simulated |
| `conversations` | assistant | patient_id, channel, started_at, handed_off_at | Confidential |
| `messages` | assistant | conversation_id, role, text, tier, source_ref, created_at | Tier: safety, lite, retrieval, model. Confidential |
| `knowledge_passages` | assistant | passage_ref, text, source_ref, review_status, language | Loaded from files under `ai/`. Every passage names its source and review status |
| `audit_log` | audit | occurred_at, actor_id, actor_type, role, action, entity_type, entity_id, patient_id, detail (JSON), outcome | Exists in code. Written on every state change and case access |

## FHIR concept mapping (design, simulated)

The mock hospital exchanges FHIR R4 resources with CareLoop over HTTP. Everything about this exchange is simulated, and no live integration is claimed.

| CareLoop | FHIR resource (concept) |
|---|---|
| patients | Patient |
| appointments | Appointment (request out, status back) |
| evidence (hospital milestones) | Encounter or Task (choose one and record it in the technical decisions) |
| consents | Consent |
| sms_messages | Communication |
| audit_log | AuditEvent |

## Seed data

`database/seeds/` will generate synthetic patients, flags, conversations and pathway events, with injected missed appointments and drop-offs. Every generated record is marked synthetic. Rates used are assumptions and are documented next to the generator.

## Open questions

- Where consent is captured (screener at invitation, or inside the first channel session).
- Whether the mock hospital keeps its own database or only an in-memory store.
- Whether `facilities` needs more than a name, type and sub-county for the demo.
""")

# --------------------------------------------------------------------------
# 4. docs/API_DOCUMENTATION.md
# --------------------------------------------------------------------------
API = "docs/API_DOCUMENTATION.md"
replace_text(API, "Every endpoint except `/health` and `/auth/login` needs a token.",
             "Every endpoint except `/health`, `/auth/login` and the simulated channel endpoints needs a token.")
replace_text(API, "Case cannot move from OPENED to TREATMENT_STARTED", "Case cannot move from FLAGGED to HANDED_OFF")
replace_text(API, '{ "to_state": "PATIENT_NOTIFIED", "note": "Message approved and sent (simulated)" }',
             '{ "to_state": "ENGAGED", "note": "Person joined through the simulated USSD menu" }')
sub_line(API, "| Screenings |",
         "| Screenings | `POST /patients/{id}/screenings` | Screener records a concerning finding (not a diagnosis); with consent this opens a case | clinician, coordinator |")
sub_line(API, "| Cases | `POST /cases/{id}/evidence`",
         "| Cases | `POST /cases/{id}/evidence` | Attach evidence; hospital milestones from the mock hospital are stored as evidence | clinician, coordinator |")
sub_line(API, "| Cases | `POST /cases/{id}/close`",
         "| Cases | `POST /cases/{id}/close` | Needs a hospital milestone or a recorded human decision with a reason | clinician, coordinator |\n| Cases | `POST /cases/{id}/claim` | Take ownership of a case | coordinator, clinician |\n| Cases | `POST /cases/{id}/mark-lost` | Record a human decision that the person is lost to follow-up, after navigator attempts | coordinator, clinician |")
sub_line(API, "| Referrals | `POST /cases/{id}/referrals`",
         "| Barriers | `GET /cases/{id}/barriers`, `POST /barriers/{id}/confirm` | List detected barriers; the person's confirmation lets a navigator see them | coordinator, patient (via channel) |")
sub_line(API, "| Referrals | `POST /referrals/",
         "| Assistant | `POST /assistant/message` | Web chat: safety rules, then Lite mode, then retrieval. Crisis text returns a human handoff | patient |")
sub_line(API, "| Tasks |",
         "| Tasks | `GET /navigator/tasks`, `PATCH /navigator/tasks/{id}` | Navigator worklist; tasks are created by the system or by a navigator | coordinator |")
sub_line(API, "| Appointments |",
         "| Appointments | `POST /cases/{id}/appointments/request`, `PATCH /appointments/{id}` | Request a visit, confirm, mark attended or missed; a missed visit creates a navigator task | coordinator |")
sub_line(API, "| Notifications | `POST /cases/{id}/notifications/draft`",
         "| Channels | `POST /channels/ussd` | Simulated USSD callback: session, phone reference and text in, menu screen out | public (simulator) |")
sub_line(API, "| Notifications | `GET /notifications",
         "| Channels | `POST /channels/sms/inbound` | Simulated inbound SMS: reply codes 1, 2, 3 and STOP | public (simulator) |")
sub_line(API, "| Notifications | `POST /notifications/{id}/approve`",
         "| Channels | `GET /sim/sms-outbox` | Simulated SMS outbox shown in the simulator; an undelivered message creates a navigator task | public (simulator) |")
sub_line(API, "| Notifications | `POST /notifications/{id}/acknowledge`",
         "| Interop | `POST /interop/appointment-request`, `POST /interop/milestones` | Send a FHIR Appointment request to the mock hospital; receive milestones back (stored as case evidence). Invalid FHIR returns 422 | system |")
drop_line(API, "| Escalations |")
sub_line(API, "| Analytics |",
         "| Analytics | `GET /analytics/summary`, `GET /analytics/funnel` | Aggregate metrics and the pathway funnel | program_manager, coordinator |")
replace_between(API, "## Stretch endpoints", "## Example: transition request", """
## Stretch endpoints

- Optional language-model mode for `POST /assistant/message` (web chat only; Lite mode stays the fallback)
- Kiswahili lexicon and templates for Lite mode (needs a fluent reviewer)
- Provider sandbox adapter for SMS or USSD (the simulator stays the default)
""")
# the old role name "coordinator" becomes "navigator" everywhere in this file
write(API, read(API).replace("coordinator", "navigator"))

# --------------------------------------------------------------------------
# 5. docs/SYSTEM_REQUIREMENTS.md
# --------------------------------------------------------------------------
REQ = "docs/SYSTEM_REQUIREMENTS.md"
sub_line(REQ, "| FR-02 |", "| FR-02 | A screener records a concerning finding (not a diagnosis); with the person's permission this opens a navigation case | P0 |")
sub_line(REQ, "| FR-06 |", "| FR-06 | Detect late or missed steps (unconfirmed reminder, undelivered SMS, missed appointment, stalled journey) on a schedule and create navigator tasks | P0 |")
sub_line(REQ, "| FR-07 |", "| FR-07 | Close a case only with a hospital milestone showing care started, or a recorded human decision with a reason | P0 |")
drop_line(REQ, "| FR-08 |")
sub_line(REQ, "| FR-09 |", "| FR-09 | Create appointment requests and navigator tasks, including for missed appointments | P0 |")
sub_line(REQ, "| FR-10 |", "| FR-10 | Send reminders from approved templates; no text or USSD screen contains a result, diagnosis or sensitive wording | P0 |")
sub_line(REQ, "| FR-11 |", "| FR-11 | Simulate USSD and SMS through a channel simulator, with reply codes 1 (confirm), 2 (change), 3 (help) and STOP | P0 |")
sub_line(REQ, "| FR-12 |", "| FR-12 | Navigator dashboard showing open tasks, stalled cases and the pathway funnel | P0 |")
sub_line(REQ, "| FR-14 |", "| FR-14 | Navigator task queue showing confirmed barriers and a suggested next step | P0 |")
sub_line(REQ, "| FR-16 |", "| FR-16 | Purpose-specific, revocable consent (invitation, SMS contact, sharing barriers with a navigator) | P0 |")
sub_line(REQ, "| FR-17 |", "| FR-17 | Audit log of every state change, access to a case, and assistant handoff to a human | P0 |")
sub_line(REQ, "| FR-18 |", "| FR-18 | Metrics: pathway funnel, time between stages, missed appointments, opt-outs, open tasks | P1 |")
sub_line(REQ, "| FR-20 |", "| FR-20 | Evaluation sets with written-up results: Lite mode precision and recall, crisis-detection recall, USSD and SMS length limits | P1 |")
drop_line(REQ, "| FR-21 |")
drop_line(REQ, "| FR-22 |")
sub_line(REQ, "| FR-23 |", """| FR-23 | Exchange FHIR R4 resources with a mock hospital process (appointment request out, milestones in); labelled simulated | P0 |
| FR-24 | Safety rules run before any other assistant step: crisis language and requests for a diagnosis produce a human handoff | P0 |
| FR-25 | Lite mode: menus plus keyword and phrase matching to approved messages, with no model | P0 |
| FR-26 | Barrier detection (fear, cost, transport, stigma, not knowing where to go); only barriers the person confirms reach a navigator | P0 |
| FR-27 | Knowledge base of approved passages, each with a source and review status; grounded retrieval shows the source or says it was not found | P0 |
| FR-28 | Small synthetic facility directory used to suggest where to go | P1 |
| FR-29 | Handoff and loop closure: arrival confirmed, hospital milestones watched, case closes when care has started | P0 |
| FR-30 | A person can opt out at any point; the choice is recorded and respected, and STOP is honoured immediately | P0 |
| FR-31 | Patient web view with chat and journey | P1 |""")
sub_line(REQ, "| NFR-02 |", "| NFR-02 | Works without any language model: safety rules, Lite mode and retrieval need no model or external call | P0 |")
insert_after_line(REQ, "| NFR-12 |", "| NFR-13 | SMS and USSD text stays within channel length limits and never contains sensitive wording | P0 |")
replace_between(REQ, "## Users (roles are permissions, not people)", "## Assumptions to revisit", """
## Users (roles are permissions, not people)

- **Patient:** chats on the web or uses the simulated USSD and SMS channels; no staff login.
- **Navigator:** works the task list, calls people, explains costs, helps with transport, finds a clinic. Sees only barriers the person confirmed.
- **Counsellor:** takes over when the assistant hands off a distressed person.
- **Clinician:** confirms arrival and records hospital milestones in the demo.
- **Program manager:** sees aggregate metrics and audit summaries.
- **Admin:** manages users and configuration in the demo.
""")

# --------------------------------------------------------------------------
# 6. docs/ARCHITECTURE.md
# --------------------------------------------------------------------------
write("docs/ARCHITECTURE.md", """
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
""")

# --------------------------------------------------------------------------
# 7. docs/SECURITY_AND_PRIVACY.md
# --------------------------------------------------------------------------
SEC = "docs/SECURITY_AND_PRIVACY.md"
replace_between(SEC, "## Roles and permissions (demo design)", "The exact stage permissions", """
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

The patient has no staff login. Patients use the web chat or the simulated USSD and SMS channels.""")
sub_line(SEC, "## Audit logging", """
## Privacy for messages

- No result, diagnosis or sensitive wording appears in any SMS or USSD screen, because phones are often shared.
- Reminders show only a time and place, with reply codes 1 (confirm), 2 (change), 3 (help) and STOP.
- STOP and "I do not want to continue" are honoured immediately and recorded.
- Confidential conversations are stored apart from case tables. Only what the person agrees to share reaches a navigator.

## Audit logging""")
replace_text(SEC, "AI drafts are logged with `actor_type = ai` and the reviewer who approved or rejected them.",
             "Assistant actions, including handoffs to a human, are logged with `actor_type = ai` and the person who took over.")
replace_between(SEC, "## Safe AI boundaries", "## Regulatory context", """
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

The old rule that every AI output goes to a human review queue no longer applies to patient chat, because replies cannot wait for staff. The controls above replace it. Safety tests (refusal, injection, impersonation, crisis wording) are documented in `docs/ai/` with results, including failures.""")
sub_line(SEC, "- Simulated messaging",
         "- Simulated USSD and SMS mean no real communication channel is tested, and shared-phone risks are handled by wording rules only.")

# --------------------------------------------------------------------------
# 8. docs/evidence/problem-and-gap.md
# --------------------------------------------------------------------------
EVI = "docs/evidence/problem-and-gap.md"
sub_line(EVI, "## Existing systems", """
## Channels and reach (to validate)

| Claim | Status | Source |
|---|---|---|
| Clinicians report fear, stigma, cost and not knowing where to go as reasons people do not reach assessment | [A] preliminary observations, not proven national findings | clinician conversations |
| A real USSD short code needs licensing through the Communications Authority and mobile networks | [A] stated in the README, not yet sourced | none yet |
| Many people CareLoop targets use basic phones with no mobile data | [A] | none yet |

## Existing systems""")
replace_between(EVI, "## Gap assessment", None, """
## Gap assessment

- **Supported [V]:** documented drop-off between positive screen and treatment; national reporting is largely aggregate.
- **Not verified [A]:** that people with a concerning finding lack patient-facing navigation that works on a basic phone, and that barriers are rarely captured before the first visit. Plausible, but no source describes routine practice at a specific facility. Validate with short interviews.
- **Positioning:** CATSystem shows tracking is being tested on the clinic side. CareLoop's intended differences (open source, support that works on a basic phone, barrier capture with the person's confirmation, a navigator handoff, FHIR-shaped exchange with hospital systems) must be confirmed against the full CATSystem protocol before being claimed.

## Next validation steps

1. Read the full CATSystem protocol and list its features.
2. Read the national cervical screening guideline for pathway steps and time windows.
3. Interview two or three people who work in the pathway (screener, nurse or navigator, records officer).
4. Ask a clinician to review the safety wording and the knowledge base passages.
""")

# --------------------------------------------------------------------------
# 9. project-management
# --------------------------------------------------------------------------
write("project-management/WORK_BREAKDOWN_STRUCTURE.md", """
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
""")

write("project-management/MILESTONES.md", """
# Milestones

Challenge deadline: **20 November 2026** (confirm the exact time on the submission form). Create these as GitHub Milestones and attach issues to them. Each milestone covers one or two of the README phases, so there is one tracker, not two.

| Milestone | Target date | README phases | Goal | Tasks |
|---|---|---|---|---|
| **M1 Foundation and core engine** | 17 Nov | 0 and 1 | Repo structured, app starts, a synthetic case moves through the pathway with an audit trail | P1, E1, E2, E3, E4, E5, D1, F1 |
| **M2 Support and channels** | 18 Nov | 2 and 3 | Safe grounded support, barrier flags, navigator tasks, simulated USSD and SMS, reminders, missed-step detection | E6, A1, A2, A3, A4, A5, C1, C2, C3, C4, F3, G7 |
| **M3 Interop and demo-ready** | 19 Nov | 4 and 5 | FHIR exchange with the mock hospital, dashboard, evaluation results, safety evidence, demo script | I1, I2, I3, F2, F4, D2, D3, G2, G3, G4, P3 |
| **M4 Submission** | 20 Nov | 6 | Fresh-machine test, video uploaded, repository and licence checked, submitted early | G5, G6, P2, P4 |

## Definition of done per milestone

- **M1:** a synthetic case can move from `FLAGGED` to `HANDED_OFF` through the API, every step is in the audit log, invalid moves are rejected, and the tests pass.
- **M2:** a synthetic patient message produces either a cited reply or a confirmed barrier flag with a navigator task; a crisis message produces a human handoff; all of this works with no language model. In the simulator someone can dial the placeholder code, flag a worry, receive a reminder and reply to confirm, and an undelivered reminder creates a navigator task.
- **M3:** an appointment request travels as FHIR to the mock hospital, milestones come back and change the case, and an invalid message is rejected with a clear error. The demo flow runs from start to finish with no manual database edits, and the evaluation results are written up.
- **M4:** a teammate runs the README steps on a clean machine; repository public with the MIT licence visible; video public on YouTube and under 3 minutes; submission form completed with time to spare.

## Rules

- Do not start stretch tasks until the milestone's P0 tasks are merged.
- At each milestone, hold a 15-minute check: what works, what slips, what to cut. Update the README phase tracker and Status table.
- Record scope cuts and phase changes in `docs/TECHNICAL_DECISIONS.md`.
""")

write("project-management/DEPENDENCIES.md", """
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
""")

# --------------------------------------------------------------------------
# 10. labels script, CONTRIBUTING, PR template
# --------------------------------------------------------------------------
LAB = "scripts/create_labels.sh"
sub_line(LAB, 'mk "ws:case-engine"', 'mk "ws:case-engine"        "1d76db" "Pathways, state machine, deadlines, tasks, audit"')
sub_line(LAB, 'mk "ws:records-referrals"', '''mk "ws:assistant"          "0e8a16" "Safety rules, Lite mode, knowledge base, retrieval, barriers"
mk "ws:channels"           "0052cc" "USSD and SMS adapters, simulator, reminders"
mk "ws:interop"            "006b75" "FHIR adapter and mock hospital"''')
sub_line(LAB, 'mk "ws:frontend"', 'mk "ws:frontend"           "5319e7" "Navigator dashboard, patient web view"')
sub_line(LAB, 'mk "ws:data-ai"', 'mk "ws:data-eval"          "fbca04" "Synthetic data, evaluation sets, safety tests"')
insert_after_line(LAB, 'mk "good-first-issue"', 'mk "idea"                  "ededed" "A proposal for the team to discuss"')

CON = "CONTRIBUTING.md"
sub_line(CON, "| Workstream |", "| Workstream | `ws:case-engine`, `ws:assistant`, `ws:channels`, `ws:interop`, `ws:frontend`, `ws:data-eval`, `ws:docs-governance`, `ws:platform` |")
sub_line(CON, "| Other |", "| Other | `blocked`, `needs-review`, `good-first-issue`, `idea` |")
sub_line(CON, "M1 Foundation (15 Nov)",
         "M1 Foundation and core engine (17 Nov), M2 Support and channels (18 Nov), M3 Interop and demo-ready (19 Nov), M4 Submission (20 Nov). See [project-management/MILESTONES.md](project-management/MILESTONES.md).")

sub_line(".github/pull_request_template.md", "- [ ] If AI is involved",
         "- [ ] If AI is involved: it never diagnoses, crisis or alarming text goes to a human, and no state changes happen without a person")

OLD_WS = "options: [case-engine, records-referrals, frontend, data-ai, docs-governance, platform]"
NEW_WS = "options: [case-engine, assistant, channels, interop, frontend, data-eval, docs-governance, platform]"
for tpl in ["bug_report.yml", "technical_task.yml", "feature_request.yml"]:
    replace_text(".github/ISSUE_TEMPLATE/" + tpl, OLD_WS, NEW_WS)

# --------------------------------------------------------------------------
# 11. README.md
# --------------------------------------------------------------------------
RD = "README.md"
replace_text(RD, "Sources will be listed in the evidence document once it is added to this repository.",
             "Sources are listed in [docs/evidence/problem-and-gap.md](docs/evidence/problem-and-gap.md).")
replace_text(RD, "are recorded in `docs/TECHNICAL_DECISIONS.md` once added.",
             "are recorded in [docs/TECHNICAL_DECISIONS.md](docs/TECHNICAL_DECISIONS.md).")
sub_line(RD, "Planned documents, linked as they are added", """
- [Architecture](docs/ARCHITECTURE.md)
- [System requirements](docs/SYSTEM_REQUIREMENTS.md)
- [Database design](docs/DATABASE_DESIGN.md)
- [API documentation](docs/API_DOCUMENTATION.md)
- [Security and privacy](docs/SECURITY_AND_PRIVACY.md)
- [Technical decisions](docs/TECHNICAL_DECISIONS.md)
- [Care pathway definition](docs/pathways/cervical-cancer.md)
- [Evidence and sources](docs/evidence/problem-and-gap.md)
- [Work breakdown](project-management/WORK_BREAKDOWN_STRUCTURE.md), [milestones](project-management/MILESTONES.md) and [dependencies](project-management/DEPENDENCIES.md)""")

# --------------------------------------------------------------------------
# 12. New folders and placeholder files
# --------------------------------------------------------------------------
for keep in [
    "frontend/.gitkeep",
    "ai/knowledge/.gitkeep",
    "ai/lexicon/.gitkeep",
    "ai/templates/.gitkeep",
    "ai/safety/.gitkeep",
    "ai/eval/.gitkeep",
    "integrations/mock_hospital/.gitkeep",
    "integrations/channel_simulator/.gitkeep",
    "integrations/sample_fhir/.gitkeep",
]:
    write(keep, "")


# --------------------------------------------------------------------------
# Commit all edits to disk
# --------------------------------------------------------------------------
changed, created = [], []
for path, text in CACHE.items():
    if ORIG.get(path) == text:
        continue
    f = ROOT / path
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text, encoding="utf-8")
    (created if ORIG.get(path) is None else changed).append(path)

print(f"Updated {len(changed)} files:")
for p in sorted(changed):
    print("  ~", p)
print(f"Created {len(created)} files:")
for p in sorted(created):
    print("  +", p)
print("\nNext: review with `git diff`, then commit and push the branch.")
