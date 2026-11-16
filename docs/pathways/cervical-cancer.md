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
