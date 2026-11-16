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
