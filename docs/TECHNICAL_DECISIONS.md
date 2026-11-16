# Technical Decisions

Lightweight decision log. Add a row when a decision changes how others work. Status values: Accepted, Proposed, Superseded.

| ID | Decision | Status | Date |
|---|---|---|---|
| TD-01 | Single monorepo named `CareLoop` | Accepted | 2026-11-14 |
| TD-02 | Modular monolith backend | Accepted | 2026-11-14 |
| TD-03 | SQLite by default, PostgreSQL later via configuration | Accepted | 2026-11-14 |
| TD-04 | Next.js, React, TypeScript, Tailwind frontend | Accepted | 2026-11-14 |
| TD-05 | Python, FastAPI, SQLAlchemy, Alembic backend | Accepted | 2026-11-14 |
| TD-06 | Care pathways defined as YAML configuration | Accepted | 2026-11-14 |
| TD-07 | Rule-based risk score first; trained model only as an offline experiment | Superseded by TD-12 | 2026-11-14 |
| TD-08 | AI drafts only, templates first, no model required to run | Superseded by TD-14 | 2026-11-14 |
| TD-09 | FHIR as a mapping design, no live exchange claimed | Superseded by TD-15 | 2026-11-14 |
| TD-10 | MIT licence | Accepted | 2026-11-14 |
| TD-11 | Pull request workflow: one approval, squash and merge | Accepted | 2026-11-14 |
| TD-12 | Scope is pre-hospital patient navigation; hospital-internal tracking (departments, referrals, treatment) is out of scope | Accepted | 2026-11-16 |
| TD-13 | USSD and SMS are simulated behind channel adapters; no live short code or provider | Accepted | 2026-11-16 |
| TD-14 | Assistant works in tiers (safety rules, Lite mode, grounded retrieval, optional model) and runs with no model | Accepted | 2026-11-16 |
| TD-15 | Mock hospital runs as a separate process and exchanges FHIR R4 resources over HTTP; everything is simulated | Accepted | 2026-11-16 |
| TD-16 | Pre-hospital pathway states: FLAGGED to CLOSED, plus OPTED_OUT and LOST_TO_FOLLOW_UP | Accepted | 2026-11-16 |
| TD-17 | Adapt the existing backend case engine on `feature/backend-case-engine` to the new pathway instead of rebuilding it | Proposed | 2026-11-16 |

## Reasons, in plain language

**TD-01 Monorepo.** Four people, one deadline. One repository means one place for issues, pull requests and documents, and no version mismatch between frontend and backend.

**TD-02 Modular monolith.** Microservices add deployment and networking work we cannot afford. Modules with strict boundaries give the same separation of work inside one program. Modules can be split later if needed.

**TD-03 SQLite.** Judges must be able to run the project. SQLite is a single file with nothing to install. The trade-off is limited concurrent writes and fewer production features, which does not matter for a demo. Using SQLAlchemy and `DATABASE_URL` keeps a PostgreSQL switch simple.

**TD-04 Next.js.** Chosen by the team. Risk: heavier tooling for beginners on a short timeline. Mitigation: keep the frontend small, a few screens, no unnecessary libraries. If it blocks progress, fall back to a simpler React setup and record that here.

**TD-05 FastAPI.** Python fits the team's skills and the ML and AI parts; FastAPI gives automatic interactive API documentation and clear data validation.

**TD-06 Pathways as YAML.** Stages, owners and deadlines are data. A new pathway is a new file, which makes "other pathways later" real and keeps clinical rules visible for review.

**TD-07 Rule-based risk score.** A model trained on synthetic data only learns the assumptions of the generator and proves nothing clinically. A transparent rule set with visible factors is more honest and easier to explain. An offline experiment in `ml/` can show how a trained model would be evaluated.

**TD-08 AI drafts only.** A hallucination in a health setting is costly. Rules live in code, patient messages come from approved templates, humans approve everything, and the system works with no model installed.

**TD-09 FHIR mapping only.** We have not verified any live integration with Kenyan systems. We design records so they can map to FHIR resources and label any export as simulated.

**TD-11 PR workflow.** One approval keeps the pace realistic over a short sprint while still giving every change a second pair of eyes.

**TD-12 Pre-hospital scope.** The README defines CareLoop as the bridge between a concerning screening finding and professional assessment. Hospitals already own diagnostics, internal referrals and treatment, and we cannot verify or integrate with those systems, so tracking them would be out of reach and a claim we cannot back. This supersedes TD-07: predictive scoring is not planned, and barrier detection comes from Lite mode plus the person's own confirmation.

**TD-13 Simulated channels.** A real short code needs licensing through the Communications Authority and mobile networks, which we have not obtained. Channel adapters keep the core and the assistant unaware of which channel a message came from, so a real provider can replace the simulator later.

**TD-14 Tiered assistant.** This supersedes TD-08. Safety rules run first. Lite mode (menus, keywords, approved messages) needs no model. Retrieval shows its source. A language model is an optional extra for web chat only. Every tier falls back to the simpler one on failure. Patient chat cannot wait for staff to approve each reply, so safety comes from approved content, refusal rules and human handoff instead of a review queue.

**TD-15 Mock hospital.** This supersedes TD-09. A separate process lets us show a real HTTP exchange of FHIR R4 resources (appointment request out, milestones back) and reject invalid messages with a clear error. It is a simulation: no live integration with any hospital system, TaifaCare, KenyaEMR or the national exchange is claimed.

**TD-16 Pathway states.** The states follow the README's ten steps and replace the hospital-side stages. OPTED_OUT records a person's decision not to continue. LOST_TO_FOLLOW_UP can only be set by a human decision. All stage deadlines are assumptions until sourced.

**TD-17 Adapt, do not rebuild.** The branch `feature/backend-case-engine` already has authentication and roles, an append-only audit log, patients and consents, screenings, a YAML-driven state machine with deadlines, escalation, closure with evidence and a human lost-to-follow-up decision, a seed script and tests. It was built for the earlier hospital-side pathway. Because stages, owners, roles and closure rules are read from `pathways/*.yaml`, most of the work is a new pathway file, renamed roles and updated tests. Status stays Proposed until the team agrees.
