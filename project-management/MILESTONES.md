# Milestones

Challenge deadline: **20 November 2026** (confirm the exact time on the submission form). Create these as GitHub Milestones and attach issues to them.

| Milestone | Target date | Goal | Tasks |
|---|---|---|---|
| **M1 Foundation** | 15 Nov | Repo structured, schema and synthetic data in place, pathway drafted | P1, E1, R1, D1, G2 |
| **M2 Core loop** | 17 Nov | A case can move through the pathway, escalate, and be audited; basic screens work | E2, E3, E4, E5, R2, R3, F1, F2, F3 |
| **M3 Demo-ready** | 19 Nov | Messaging, review queue, metrics, simulation results, safety evidence, demo script | R4, R5, F4, F5, F6, D2, D3, D4, G3, G4, P3 |
| **M4 Submission** | 20 Nov | Fresh-machine test, video uploaded, repository and licence checked, submitted early | G5, G6, P2, P4 |

## Definition of done per milestone

- **M1:** repository structure created through a reviewed pull request; the app starts; seed script produces synthetic data; pathway doc lists every stage and every unsourced deadline as assumed.
- **M2:** a seeded case can go from `OPENED` to `REFERRAL_ACCEPTED` through the API and UI; an overdue case creates an escalation; every action appears in the audit log; invalid moves are rejected.
- **M3:** one full demo story runs without manual database edits; review queue works; before/after table produced with spread reported; refusal tests recorded.
- **M4:** a teammate runs the README steps on a clean machine; repository public with MIT licence visible; video public on YouTube and under 3 minutes; submission form completed with time to spare.

## Rules

- Do not start stretch tasks until the milestone's P0 tasks are merged.
- At each milestone, hold a 15-minute check: what works, what slips, what to cut.
- Record scope cuts in `docs/TECHNICAL_DECISIONS.md`.
