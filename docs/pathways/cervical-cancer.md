# Demo Pathway: Cervical Cancer Screening-to-Care (Kenya context)

Status: **draft**. The stages follow the general shape of a screening-to-treatment pathway. **No stage deadline below has been sourced from a national guideline yet.** All deadlines are placeholders marked ASSUMED, to be replaced with guideline-sourced values (Ministry of Health national guidelines or the 2026 to 2030 elimination action plan) or kept and labelled as assumptions.

## Scope

In scope: a woman with a positive or suspicious screening result, from result to confirmatory assessment, referral, treatment initiation and follow-up.
Out of scope for the MVP: screening invitation and recall, negative-result routine recall, vaccination, branching clinical rules (for example same-day screen-and-treat), diagnosis and treatment decisions.

## Stages

| # | State | Meaning | Default owner (department) | Deadline to leave stage (ASSUMED) |
|---|---|---|---|---|
| 1 | `OPENED` | Positive or suspicious result recorded; case created | Screening clinic | Notify within 2 days |
| 2 | `PATIENT_NOTIFIED` | Result communicated (draft approved and sent) | Care coordinator | Acknowledged within 3 days |
| 3 | `PATIENT_ACKNOWLEDGED` | Patient confirmed they received the message | Care coordinator | Confirmation scheduled within 7 days |
| 4 | `CONFIRMATION_SCHEDULED` | Confirmatory assessment booked | Gynaecology clinic | Completed within 14 days |
| 5 | `CONFIRMATION_COMPLETED` | Confirmatory assessment done and documented | Gynaecology clinic | Referral or decision within 3 days |
| 6 | `REFERRAL_SENT` | Referral to treatment unit sent | Referring clinician | Accepted within 3 days |
| 7 | `REFERRAL_ACCEPTED` | Treatment unit accepted | Treatment unit | Treatment started within 14 days |
| 8 | `TREATMENT_STARTED` | Treatment or surveillance plan begun and documented | Treatment unit | Follow-up date set within 7 days |
| 9 | `FOLLOW_UP_DUE` | Post-treatment follow-up pending | Care coordinator | Follow-up completed on schedule |
| 10 | `CLOSED` | Closed with evidence | n/a | n/a |
| 11 | `LOST_TO_FOLLOW_UP` | Closed by a human decision after escalation steps | n/a | n/a |

A confirmatory result that needs no further treatment may close the case with evidence (`confirmed_negative`). A rejected referral stays in `REFERRAL_SENT` with the referral marked rejected and an escalation raised; staff create a new referral.

## Escalation rules (draft)

1. First missed deadline: escalate to the care coordinator (review queue).
2. Second missed deadline, or any case flagged urgent: escalate to a senior clinician or program manager.
3. A case moves to `LOST_TO_FOLLOW_UP` only by a recorded human decision.

## Closure evidence (draft)

`CLOSED` requires one of: documented treatment start or plan, confirmed negative confirmatory result, documented follow-up completion, or a recorded decision by an authorised clinician with a reason.

## Needs sourcing before the demo

- Real stage windows and follow-up timing from the national guideline.
- Which confirmatory and treatment steps apply in the demo setting.
- Whether a screen-and-treat branch should be modelled.

The same data lives in `pathways/cervical_cancer.yaml` (to be created) so the engine reads it from configuration.
