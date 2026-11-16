# CareLoop

**Patient navigation that helps people get from a concerning screening finding to professional care, on a smartphone or a basic phone.**

> **Status: hackathon prototype, in development.**
> Synthetic data only. CareLoop is not a medical device, has no clinical validation, is not certified by any health authority, and has **no verified integration** with any real hospital system, TaifaCare, KenyaEMR, the national health information exchange, or any mobile network. The USSD and SMS channels are **simulated**, and `*XYZ#` is a placeholder, not a real short code. CareLoop does not diagnose and is not an emergency service. If you or someone you know is in distress or in danger, contact local emergency services or a qualified professional.

## The problem

Some people who receive concerning screening information, or who notice suggestive symptoms, never reach professional assessment. Clinicians we have spoken to report reasons such as fear of a diagnosis or of painful procedures, misconceptions, stigma, cost, not knowing where to go, and a lack of emotional support. **These are preliminary observations, not proven national findings.**

Separately, published studies from Kenyan screening programmes report substantial loss to follow-up after a positive screen (one Western Kenya programme reported about 28% lost after a positive visual inspection result in 2013). These are regional studies, not current national figures. Sources will be listed in the evidence document once it is added to this repository.

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
3. **Joining, on any phone.** On a smartphone, the person can chat in a web page. On a basic phone with no data they dial a short code and pick options from a menu, and receive text messages. The help is the same; the smartphone version is richer.
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

## Status

This table is the single place that shows progress. Update it in the same pull request that finishes a piece of work.

| Component | Status | Notes |
|---|---|---|
| Case engine: stages, owners, deadlines, escalation, audit | In progress | Prototype built; being adapted to the pre-hospital pathway |
| Patient onboarding and consent | Planned | |
| Knowledge base with cited sources | Planned | Pending clinical review |
| Safety rules and human handoff | Planned | Wording needs clinical review |
| Lite mode: menus, keywords, barrier flags | Planned | English first |
| Grounded retrieval assistant (web chat) | Planned | |
| Channel layer and channel simulator (USSD and SMS) | Planned | Simulated, no live short code |
| SMS outbox, reminders, missed-step detection | Planned | |
| Barrier detection and navigation tasks | Planned | |
| Navigator dashboard and pathway funnel | Planned | |
| Mock hospital FHIR exchange | Planned | Simulated |
| Safety and quality evaluation | Planned | Our own synthetic test sets |

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

Technical decisions and their reasons are recorded in `docs/TECHNICAL_DECISIONS.md` once added. A decision can change; the record should say why.

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

Run instructions will be added here as soon as the first runnable version is merged. They must work on a clean machine without any API key.

## Documentation

Planned documents, linked as they are added: architecture, system requirements, database design, API documentation, security and privacy, technical decisions, the care pathway definition, evidence and sources, work breakdown, milestones, dependencies.

## Contributing

A full contribution guide is coming. Until then: work on a branch, open a pull request, get one approval from a teammate, never commit real patient data or secrets.

## Team notes (delete this section before submission)

- Open decisions: database default, language model access, clinical reviewer for the knowledge base and safety wording, Kiswahili reviewer, helpline information to verify, human roles, where consent is captured, simulator only or also a provider sandbox.
- Before submitting: working run instructions in "Getting started", links in "Documentation" all working, Status table up to date, licence visible in the repository's About section, demo video public on YouTube, no secrets in the repository history.

## Licence

MIT. See `LICENSE`.
