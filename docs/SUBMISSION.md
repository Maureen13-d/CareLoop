# Submission: closing the screening-to-care gap

Future Health Digital Innovation Challenge. Prototype, 20 Nov 2026. All data are synthetic.

## Problem

People get screened. A result needs a visit. In many Kenyan facilities nobody has a protocol for what happens next, so the person never arrives and the problem gets worse. Community health workers are already overstretched. They need a short list: who to chase, why, and what to do.

## What CareLoop does

A clinician records the screening. If the finding is concerning or urgent and the person consents, CareLoop issues a random ID and follows that person until a facility confirms they arrived.

The CHW worklist ranks assigned people. A report of worse symptoms is always first. Each row has a reason ("not arrived, 9 days", "barrier: transport fare") and one recommended action from a fixed list: call, home visit, transport support, counsellor, or escalate to a clinician.

The person can use a web card, a Telegram simulator, or the USSD contract. All three call the same rules. The guide on the web card speaks those rules and nothing else.

## What it refuses to do

It does not diagnose, stage an illness, or say that someone is fine. It does not mark arrival. It does not decide that someone is lost. Those are human actions. Unclear messages go to a person.

## Simulated versus real

| Simulated | Real in this repo |
|---|---|
| People, phones, facilities, the 200-person cohort | The pathway rules, the ID check digit, the second code, the worklist ranking |
| Telegram delivery, SMS delivery, USSD gateway | The conversation core and the contract a gateway would call |
| The one-time code, shown on a staff screen | Expiry, single use, lockout, identical errors for unknown IDs |
| The clinic that can confirm arrival | The rule that only staff or that simulator can do it |

## Assumptions

- Deadlines and the two-day check-in are labelled assumed. They are not a guideline.
- Quiet hours are 21:00 to 07:00 on the demo clock.
- A shared phone is normal, so outbound messages do not name the condition or the screening type.
- English and Kiswahili lines are drafts pending clinical review.

## Pilot path

One county, one primary care network, one facility.

Before any of that: clinical review of the lines and the danger-sign list, a data-protection assessment (the ID plus a contact is still personal data), a real messaging provider, and a real facility system instead of the simulator. Hardware that prints the slip offline is described in `docs/HARDWARE_NEXT.md` and is not part of this build.

## How to judge the demo

`docs/DEMO_SCRIPT_SCREENING.md` is the four-minute path. The maternal demo in `docs/DEMO_SCRIPT.md` is an earlier pathway and is not this story.
