# CareLoop

**Care-pathway orchestration layer for screening-to-care follow-up.**
Hackathon MVP for the Future Health Digital Innovation Challenge (Challenge 05: Closing the Screening-to-Care Loop).

> **Status: planning and scaffolding.** The repository currently holds the design and documentation. Application code is being built. Nothing listed under "Planned features" is implemented until its box is ticked.
>
> **Synthetic data only.** CareLoop is not a medical device, has no clinical validation, and has **no verified integration** with any real hospital system, KenyaEMR, Afya Yangu or the national health information exchange.

## The problem

When a woman screens positive for cervical pre-cancer, care depends on several steps across departments and often across facilities: communicating the result, confirmatory assessment, referral, treatment and follow-up. Studies in western Kenya report substantial loss to follow-up along this path (for example, 27.9% after a positive VIA screen and 49.3% between biopsy and LEEP in one 2013 programme). National reporting is largely aggregate counts, and we found no source describing routine patient-level tracking with named owners and deadlines across departments. See [docs/evidence/problem-and-gap.md](docs/evidence/problem-and-gap.md) for sources and for what is verified versus assumed.

## What CareLoop does

CareLoop sits **on top of** existing hospital systems; it does not replace them. Each positive screening result becomes a **case** with an owner, a deadline, an escalation path and a required evidence trail before it can close. Software watches the clocks and raises escalations to humans. AI can only **draft** messages and summaries for staff to approve. Staff make every clinical and closure decision.

First demonstration pathway: **cervical cancer screening-to-care** (Kenya context). The design allows other pathways to be added as configuration.

## Planned features (MVP)

- [ ] Case engine: stages, owners, deadlines, evidence-based closure
- [ ] Escalation engine with a demo clock
- [ ] Patient, screening, referral, task and appointment records (synthetic)
- [ ] Coordinator dashboard: overdue, stuck and unowned cases
- [ ] Human review queue for drafted patient messages and escalations
- [ ] Simulated patient notification outbox with acknowledgement
- [ ] Role-based access, consent records and an audit log
- [ ] Synthetic data generator and before/after simulation
- [ ] Rule-based missed-care risk score
- [ ] AI drafting assistant with controlled tools and template fallback (stretch)
- [ ] FHIR mapping and mock export (stretch, clearly labelled simulated)

## Technology

Next.js, React, TypeScript, Tailwind CSS (frontend); Python and FastAPI (backend, modular monolith); SQLite by default via SQLAlchemy and Alembic; pytest; optional Docker Compose. Reasons are in [docs/TECHNICAL_DECISIONS.md](docs/TECHNICAL_DECISIONS.md).

## Getting started

Setup and run instructions will be added here once the application skeleton exists. They must work on a clean machine with no API keys.

## Documentation

| Document | Purpose |
|---|---|
| [ARCHITECTURE](docs/ARCHITECTURE.md) | System design and module boundaries |
| [SYSTEM_REQUIREMENTS](docs/SYSTEM_REQUIREMENTS.md) | Functional and non-functional requirements |
| [DATABASE_DESIGN](docs/DATABASE_DESIGN.md) | Tables and relationships |
| [API_DOCUMENTATION](docs/API_DOCUMENTATION.md) | API conventions and endpoints |
| [SECURITY_AND_PRIVACY](docs/SECURITY_AND_PRIVACY.md) | Privacy, consent, access, audit, AI boundaries |
| [TECHNICAL_DECISIONS](docs/TECHNICAL_DECISIONS.md) | Key decisions and reasons |
| [Cervical pathway](docs/pathways/cervical-cancer.md) | Demo pathway stages |
| [Evidence](docs/evidence/problem-and-gap.md) | Sources and verification status |
| [Work breakdown](project-management/WORK_BREAKDOWN_STRUCTURE.md), [Milestones](project-management/MILESTONES.md), [Dependencies](project-management/DEPENDENCIES.md) | Planning |
| [CONTRIBUTING](CONTRIBUTING.md) | How we work in this repository |

## Licence

MIT. See [LICENSE](LICENSE).
