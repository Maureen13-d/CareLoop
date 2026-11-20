# CareLoop

**Patient navigation that helps people get from a concerning screening finding to professional care, on a smartphone or a basic phone.**

> **Status: hackathon prototype, in development.**
> Synthetic data only. CareLoop is not a medical device, has no clinical validation, is not certified by any health authority, and has **no verified integration** with any real hospital system, TaifaCare, KenyaEMR, the national health information exchange, or any mobile network. The USSD and SMS channels are **simulated**, and `*XYZ#` is a placeholder, not a real short code. CareLoop does not diagnose and is not an emergency service. If you or someone you know is in distress or in danger, contact local emergency services or a qualified professional.

## The problem

Some people who receive concerning screening information, or who notice suggestive symptoms, never reach professional assessment. Clinicians we have spoken to report reasons such as fear of a diagnosis or of painful procedures, misconceptions, stigma, cost, not knowing where to go, and a lack of emotional support. **These are preliminary observations, not proven national findings.**

Separately, published studies from Kenyan screening programmes report substantial loss to follow-up after a positive screen (one western Kenya programme reported about 28% lost after a positive visual inspection result in 2013). These are regional studies, not current national figures. Sources will be listed in the evidence document once it is added to this repository.

## What CareLoop does, and where it stops

| | |
|---|---|
| **CareLoop focuses on** | Education, a supportive conversation, barrier detection, navigation to care, appointment requests and reminders, and pre-assessment tracking |
| **Hospital systems own** | Diagnostics, internal referrals, departmental tasks, treatment and clinical follow-up |
| **CareLoop only watches** | A few coarse milestones after the patient is inside the hospital's care, so nobody disappears between arriving and care starting |

CareLoop complements hospital systems. It does not replace them.

## How it works, from start to finish

1. **Screening.** A person has a screening and the result is concerning. This is not a diagnosis. It means a proper check is needed.
2. **Invitation.** The screener records the finding and, with the person's permission, invites them to CareLoop. They can say no.
3. **Joining, on any phone.** On a smartphone the person can chat in a web page. On a basic phone with no data they dial a short code and pick options from a menu, and receive text messages. The help is the same; the smartphone version is richer.
4. **Support and answers.** The assistant answers questions in plain language from a library of approved information with visible sources, clears up myths and offers general reassurance. It never tells someone they have a disease, recommends treatment or discourages assessment. If the person seems distressed, or writes something alarming, it stops and hands over to a human.
5. **Worries are picked up.** As the person talks or taps menu options, CareLoop notices what may be holding them back: fear, cost, transport, stigma or not knowing where to go. It asks them to confirm. Only what they agree to share reaches a human helper (a navigator).
6. **A navigator steps in.** The navigator sees the confirmed worries and a suggested next step, and does what software cannot: calls the person, explains costs, helps with transport, finds a clinic.
7. **The visit is arranged.** An appointment request goes to the clinic, which confirms. The person gets a short, discreet text with the time and place. It never mentions a result, because phones are often shared. They can reply to confirm, change, or ask for help.
8. **CareLoop keeps watch.** An unconfirmed reminder, an undelivered text or a missed appointment creates a follow-up task for a navigator. Missing an appointment is treated as a problem to solve, not a failure by the patient.
9. **Handoff.** Once the clinic confirms arrival, the hospital's own systems and staff take over all clinical care. CareLoop steps back.
10. **A light check that no one is lost.** CareLoop looks only for a few milestones from the hospital, such as assessment completed and care started. If nothing arrives for too long, a navigator checks in. When care has started, the case closes.

A person can decide not to continue at any point. That choice is recorded and respected.

**Automatic:** reminders, noticing late or missed steps, creating tasks, recording every step.
**Always a human:** clinical decisions, handling distress, deciding someone is lost to follow-up, closing a case without evidence.

## Three technology areas

**1. AI engineering: a supportive, grounded assistant that works on every channel.**
The assistant works in tiers and always falls back to the simpler one if something fails:

| Tier | What it does | Needs | Used on |
|---|---|---|---|
| Safety rules | Detect crisis language and requests for a diagnosis, before anything else | Nothing | Every channel |
| **Lite mode** | Menus plus keyword and phrase matching to approved messages; produces barrier flags | Nothing: no model, no internet calls | USSD, SMS, and as web fallback |
| Grounded retrieval | Searches the approved knowledge base and shows the source | Nothing | Web chat, and "more information by SMS" |
| Language model (optional) | Rephrases retrieved passages for web chat | Model access | Web chat only |

"Offline" here means the patient needs no smartphone or mobile data, and Lite mode needs no model or external service. Our server still has to be reachable by the network gateway.

**2. Software engineering: navigation and workflow.**
A rule-driven engine turns a screening finding into a tracked journey with owners and deadlines. It detects missed appointments and stalled journeys, creates tasks for navigators, sends reminders, escalates, and shows where people drop out. Automation here is deterministic and explainable.

**3. Interoperability: a bridge to existing systems.**
CareLoop speaks FHIR R4. For the prototype, a **mock hospital system** exchanges FHIR resources with CareLoop over HTTP. Everything about this exchange is simulated.

## Reaching people without smartphones (USSD and SMS)

- **USSD** is the "dial a short code and pick from a menu" channel that works on any phone without data. An example menu: my next step, questions, I have a worry, my appointment, call me back, I need to talk to someone now.
- **SMS** carries short reminders with reply codes (1 to confirm, 2 to change, 3 for help, STOP to opt out) and approved information on request.
- **Privacy by default:** no result, diagnosis or sensitive wording appears in any text or USSD screen.
- **Reliability rules:** an undelivered or unanswered reminder creates a navigator task; STOP is honoured immediately.
- **In the prototype** both channels run through a **channel simulator** (a small page showing a feature-phone screen and a text inbox). A real short code requires licensing through the Communications Authority and mobile networks, which we have not obtained.

## Development phases

We build in phases so everyone can see how far we are. **Phases overlap, because several people work in parallel. A phase is done when its exit criteria are met, not when its date passes.** Dates are targets for the 20 November prototype deadline. Phases can be merged, split, added or dropped by team agreement; note the change and the reason in the technical decisions record.

**Current focus: the pathway, desk, chat, phone simulator and simulated clinic handoff run on synthetic data. The demo video has not been recorded, and the knowledge base is still awaiting clinical review.**

| Phase | Goal | Target | Status |
|---|---|---|---|
| 0. Foundation and alignment | Shared scope, working repository, everyone able to contribute | 16 Nov | Done |
| 1. Core engine and data | A synthetic case moves through the pre-hospital pathway with owners, deadlines and an audit trail | 16 to 17 Nov | Done |
| 2. Support and navigation | Safe, grounded support, barrier flags and navigation tasks that work with no model | 17 Nov | Done |
| 3. Channels and follow-up | USSD and SMS (simulated), reminders, missed-step detection | 17 to 18 Nov | Done |
| 4. Interoperability and handoff | FHIR exchange with a mock hospital; handoff and loop closure | 18 Nov | Done |
| 5. Dashboard, evaluation and hardening | Navigator dashboard and funnel, evaluation results, safety testing | 18 to 19 Nov | Done |
| 6. Demo and submission | Fresh-machine test, video, description, final checks, submit | 19 to 20 Nov | Not started |

Status values: **Not started**, **In progress**, **Done**, **Dropped**.

### Phase 0: Foundation and alignment
- [x] Scope agreed: pre-hospital bridge, USSD and SMS channels, Lite mode
- [x] README merged and the repository About section updated
- [ ] Labels, milestones, project board and the `idea` label created
- [ ] Open decisions resolved or defaulted (a clinical reviewer for the knowledge base is still needed)
- [x] Backend foundation merged

**Done when:** every teammate has cloned the repository, run it, and opened a pull request.

### Phase 1: Core engine and data
- [x] Pre-hospital pathway definition (flagged, engaged, barriers assessed, navigation, appointment booked, arrival confirmed, handed off, closed)
- [x] Roles: patient, navigator, counsellor, clinician, program manager, admin
- [x] Consent purposes, including SMS contact and sharing barriers with a navigator
- [x] Synthetic seed data
- [x] Tests updated and passing

**Done when:** a synthetic case can move from flagged to handed-off through the API, every step is in the audit log, and the tests pass.

### Phase 2: Support and navigation
- [x] Knowledge base v1: about 20 to 30 passages, each with its source and review status
- [x] Safety rules (crisis language, requests for a diagnosis) with human handoff
- [x] Lite mode: menus, keyword lexicon, barrier flags
- [x] Grounded retrieval for web chat
- [x] Navigation tasks and a small synthetic facility directory

**Done when:** a synthetic patient message produces either a cited, grounded reply or a confirmed barrier flag with a navigator task; a crisis message produces a human handoff; and all of this works with no language model installed.

### Phase 3: Channels and follow-up
- [x] Channel layer and channel simulator (USSD menu, SMS inbox)
- [x] SMS outbox with approved templates, reply codes and STOP
- [x] Appointment requests and reminders
- [x] Missed-appointment and unreachable-by-SMS detection

**Done when:** in the simulator someone can dial the placeholder code, flag a worry, receive a reminder and reply to confirm, and an undelivered reminder creates a navigator task.

### Phase 4: Interoperability and handoff
- [x] FHIR mapping and the adapter interface
- [x] Mock hospital system running as a separate process
- [x] Appointment request sent out; arrival and milestones received back
- [x] Handoff and loop closure

**Done when:** an appointment request travels as FHIR to the mock hospital, milestones come back and change the case, and an invalid message is rejected with a clear error.

### Phase 5: Dashboard, evaluation and hardening
- [x] Navigator dashboard with a pathway funnel
- [x] Patient web view (chat and journey)
- [x] Evaluation sets and written-up results (Lite mode precision and recall, crisis detection recall, USSD and SMS length limits)
- [x] Safety and refusal tests documented, including failures
- [x] Documents consistent with the code; Status table accurate

**Done when:** the demo flow runs from start to finish with no manual database edits, and the evaluation results are written up.

### Phase 6: Demo and submission
- [ ] Run instructions tested on a clean machine
- [ ] Demo script and video (under 3 minutes, public on YouTube)
- [ ] Text description and tools list
- [ ] Final repository checks: licence visible, no secrets, links working, Team notes removed
- [ ] Submitted early

**Done when:** the submission form is complete and confirmed.

## Status

This table is the single place that shows progress by component. Update it in the same pull request that finishes a piece of work, and update the phase tracker above at each milestone check.

| Component | Phase | Status | Notes |
|---|---|---|---|
| Case engine: stages, owners, deadlines, escalation, audit | 1 | Working | Pre-hospital pathway in `pathways/cervical_cancer.yaml` |
| Patient onboarding and consent | 1 | Working | Clinician intake screen records consent, then a finding |
| Knowledge base with cited sources | 2 | Working | 20 draft passages; pending clinical review |
| Safety rules and human handoff | 2 | Working | Crisis, distress, symptoms and diagnosis requests |
| Lite mode: menus, keywords, barrier flags | 2 | Working | English. Confirmed worries open a navigator task |
| Grounded retrieval assistant (web chat) | 2 | Working | Web only. SMS and USSD stay on short templates |
| Barrier detection and navigation tasks | 2 | Working | Keyword matches stay private until the person confirms |
| Channel layer and channel simulator (USSD and SMS) | 3 | Working | Simulated. `*XYZ#` is a placeholder |
| SMS outbox, reminders, missed-step detection | 3 | Working | Reply 1/2/3/STOP. Undelivered text opens a task |
| Mock hospital FHIR exchange | 4 | Working | Simulated clinic on port 8100. The desk can request a visit and read milestones |
| Navigator dashboard and pathway funnel | 5 | Working | Today, cases, chat, phone, follow-up, audit |
| Loop-closure metrics | 5 | Working | `GET /metrics`, shown on Follow-up. Synthetic associations, not causal claims |
| Safety and quality evaluation | 5 | Working | Test-split write-up in `docs/EVALUATION.md`. Crisis recall on that set is 25% |

Status values: **Planned**, **In progress**, **Working** (runs and has tests), **Dropped**.

## Scope

**Core (committed for the demo):** onboarding and consent, the pre-hospital pathway, the assistant with safety rules, Lite mode and a cited knowledge base, the simulated USSD and SMS channels, barrier capture and navigation tasks, appointment requests with reminders, the navigator dashboard, and the mock FHIR exchange.

**Exploring (we may add these if time and need allow):** a language model mode for web chat, Kiswahili support, testing against a provider sandbox, embedding-based search, a larger facility directory, additional FHIR resources, further care pathways, richer analytics.

**Not planned for now:** hospital-internal tracking (departmental tasks, diagnostics, treatment), predictive machine learning, fine-tuning, live integrations, a live short code or real messaging, a counselling network.

New ideas are welcome. See "Designed to grow" below.

## Principles that stay fixed

- **Synthetic data only.** No real patient information anywhere in this repository.
- **Humans decide.** AI drafts, explains and supports. People make clinical, closure and escalation decisions.
- **AI educates, never diagnoses.**
- **Reach.** Core navigation must not depend on a smartphone or mobile data.
- **Honest claims.** We separate what is verified from what is assumed, and we do not claim clinical outcomes, certification or live integrations we do not have.
- **Privacy by design.** Purpose-specific consent, minimal data, discreet messages, confidential support conversations kept separate and access-controlled, an audit trail.

## Technology (current choices, open to change)

- **Frontend:** Next.js, React, TypeScript, Tailwind CSS
- **Backend:** Python, FastAPI, SQLAlchemy, a modular monolith
- **Database:** SQLite by default so the project runs anywhere; written so another database can be used later
- **AI:** safety rules and Lite mode first, retrieval over a curated knowledge base, an optional language model behind a swappable interface
- **Channels:** simulated USSD and SMS behind adapters, so a real provider can be added later
- **Interoperability:** HL7 FHIR R4
- **Testing:** pytest, with frontend tests where useful
- **Optional:** Docker

Technical decisions and their reasons are recorded in [docs/TECHNICAL_DECISIONS.md](docs/TECHNICAL_DECISIONS.md). A decision can change; the record should say why.

## Designed to grow

- **A new care pathway:** add a definition file under `pathways/`. Stages, owners, deadlines and closure rules are configuration, not code.
- **New knowledge for the assistant:** add a passage with its source reference. Every passage names where it came from and its review status.
- **New keywords or a new language for Lite mode:** add to the lexicon files under `ai/`, reviewed by a fluent speaker.
- **A new channel (for example WhatsApp):** add a channel adapter. The core and the AI do not know which channel a message came from.
- **A real SMS or USSD provider:** implement the provider interface.
- **A new external system:** implement the adapter interface in the interoperability module.
- **A new feature area:** add a backend module. A module reads and writes only its own tables and talks to others through their service functions.

To propose something new: open an issue and label it `idea`. When the team agrees, assign it to a milestone and add it to the Status table above.

## Repository layout

Folders appear as the work starts. This is the intended shape, not a promise that every folder exists yet.

```
backend/        API, case engine, channel adapters and feature modules
frontend/       patient web app and navigator dashboard
pathways/       care pathway definitions
ai/             knowledge base, lexicons, templates, safety rules, evaluation sets
integrations/   mock hospital system, channel simulator, sample FHIR messages
database/       seed data (synthetic)
docs/           architecture, requirements, design and evidence
project-management/   work breakdown, milestones, dependencies
.github/        issue and pull request templates
```

## Getting started

You need Python 3.11+ and Node 20+. No API key.

```bash
# Backend (from backend/)
uv venv .venv --python 3.12
uv pip install -e ".[dev]" --python .venv/Scripts/python.exe
.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000

# Frontend (from frontend/)
npm install
npm run dev
```

On macOS or Linux, the Python path is `.venv/bin/python` instead of `.venv/Scripts/python.exe`.

Open http://localhost:3000 and sign in as **amina** (navigator), **david** (clinician), **aisha** (patient) or **grace** (community health promoter). Every demo account uses the password `careloop-demo`. The first backend start seeds synthetic people across the cervical pathway and the maternal pathway. Restarting keeps that data. Delete `backend/careloop.db` to seed again.

The phone at `/phone` is a simulator. `*XYZ#` is not a real short code.

The simulated clinic is a separate process. Start it from the repository root, so Python can import `integrations`:

```bash
backend/.venv/Scripts/python -m uvicorn integrations.mock_hospital.app:app --port 8100
```

On macOS or Linux that interpreter is `backend/.venv/bin/python`. The desk's "Simulated clinic" card talks to this process. If it is not running, the request fails with a clear message. It is not a real hospital.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [System requirements](docs/SYSTEM_REQUIREMENTS.md)
- [Database design](docs/DATABASE_DESIGN.md)
- [API](docs/API_DOCUMENTATION.md)
- [Security and privacy](docs/SECURITY_AND_PRIVACY.md)
- [Data policy](docs/DATA_POLICY.md)
- [Technical decisions](docs/TECHNICAL_DECISIONS.md)
- [Clinical review brief](docs/CLINICAL_REVIEW.md) (parameters are still unreviewed)
- [Evaluation results](docs/EVALUATION.md)
- [Pathway](docs/pathways/cervical-cancer.md)
- [Evidence](docs/evidence/problem-and-gap.md)
- [Work breakdown](project-management/WORK_BREAKDOWN_STRUCTURE.md)
- [Milestones](project-management/MILESTONES.md)
- [Dependencies](project-management/DEPENDENCIES.md)

## Contributing

Work on a branch, open a pull request, get one approval from a teammate, and never commit real patient data or secrets.

## Licence

MIT. See `LICENSE`.

## Persistence
State lives in SQLite (`backend/careloop.db`, gitignored) via SQLModel. Tables are created on startup
and synthetic data is seeded **only if the database is empty**, so restarting never loses state.

    python -m app.cli reset --demo    # wipe and re-seed (+ scripted escalated case) before a demo
    python -m app.cli status          # row counts

Override the location with `CARELOOP_DATABASE_URL`. Tests always use an in-memory database.
The domain logic is storage-agnostic: `app/repository.py` is the only place that touches rows.

## Metrics
`GET /metrics` returns loop-closure rate, escalation rate, recovery after escalation, contacts to
attendance, and time to referral; they are shown on `/outreach`. An *episode* is one overdue stage
of one case that received at least one contact. Rates are associations, not causal claims, and
contacted vs uncontacted cases are deliberately not compared (outreach only starts once a case is
already late). Stage changes happen only through `POST /outreach/cases/{id}/respond`, so every
change is recorded and counted. All figures are computed from synthetic data.

## Clinical review status
**Unreviewed.** Stage timeframes, the outreach ladder, the contact gap and the message wording are
engineering placeholders. They have not been checked by a clinician and must not be used for any
clinical or operational decision. The review brief is in
[docs/CLINICAL_REVIEW.md](docs/CLINICAL_REVIEW.md); its parameter tables are generated from the code
(`python -m app.clinical_params`) and a test fails if they drift apart.
