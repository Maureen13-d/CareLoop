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
| TD-07 | Rule-based risk score first; trained model only as an offline experiment | Accepted | 2026-11-14 |
| TD-08 | AI drafts only, templates first, no model required to run | Accepted | 2026-11-14 |
| TD-09 | FHIR as a mapping design, no live exchange claimed | Accepted | 2026-11-14 |
| TD-10 | MIT licence | Accepted | 2026-11-14 |
| TD-11 | Pull request workflow: one approval, squash and merge | Accepted | 2026-11-14 |

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
