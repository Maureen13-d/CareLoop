# CareLoop Maternal

CareLoop Maternal is a second pathway on the same engine as the cervical journey. It is a synthetic prototype for a community health promoter, a navigator, and a simulated clinic. It does not diagnose, treat, or run a hospital.

Clinical rules and reply text are **PENDING CLINICAL REVIEW**. Deadlines in `pathways/maternal.yaml` are marked **ASSUMED**.

## Why this pathway exists

WHO's maternal mortality fact sheet (7 April 2025) describes about 260,000 maternal deaths in 2023, more than 700 a day, with about 92% in low and lower-middle income countries and about 70% in sub-Saharan Africa. A large share are from severe bleeding, infection, pre-eclampsia and eclampsia, delivery complications, and unsafe abortion. The World Bank series SH.STA.MMRT gives Kenya a maternal mortality ratio of 149 per 100,000 live births for 2023.

Two studies shape what this prototype refuses to claim. CRADLE-3 (Vousden and colleagues, Lancet Global Health 2019, PMID 30784635) did not show that a blood-pressure device strategy reduced deaths after adjustment. The Jacaranda PROMPTS cluster trial (PLoS Medicine 2025, PMID 39899612) found small gains in knowledge and preparedness and no significant effect on danger-sign care seeking. An informal-settlement study (BMC 2024, PMID 38539140) found enrolled mothers more likely to report four or more antenatal contacts. CareLoop copies the navigation idea, not a claim of reduced deaths.

## What the software does

A promoter enrols a woman who has agreed to care coordination. A cuff reading or a scripted check-in runs through `rules/maternal_triage.yaml`. The server, not the hub, sets green, yellow, or red. Missing or unreadable numbers are never green. Red opens one urgent task and moves the journey to "needs a person" on the shorter assumed deadline. A band SOS does the same. A band heart-rate, oxygen, inactivity, or battery event never opens a journey and never changes the colour. It asks for a cuff reading or a charge.

Yellow asks whether she wants a call before a task is opened. Crisis and distress language hands the message to a person before any other reply.

A human decides distress handling, lost follow-up, and closure. The promoter cannot move clinical states and sees only women assigned to her.

Texts stay short and avoid words that would expose a pregnancy on a shared phone. Swahili templates exist for every English one. The cervical phone menu is unchanged. A maternal check-in on USSD starts only when someone sends `M`.

Transport help is `SIMULATED_MPESA` with the amount label `assumed`. A cover check is `SIMULATED_SHA`. Neither is a live payment or a live SHA lookup.

The clinic bridge reuses the mock hospital. An antenatal request is described as `SYNTHETIC: antenatal visit request` and advances `arrived` → `antenatal_visit_completed` → `care_plan_recorded`. Those map to the states `arrived` and then `with_hospital`. The cervical milestones are unchanged.

## Roles

| Person | Username | What they can do |
|---|---|---|
| Grace Achieng, promoter | grace | Her own women, a cuff reading, a check-in, lend or return a band |
| Amina Otieno, navigator | amina | Barriers, the simulated voucher and cover check, booking a visit |
| David Kamau, clinician | david | Arrival and the hospital's own steps |
| Peter Omondi, program manager | peter | Counts and the audit, which stores labels rather than a woman's words |

The demo password is `careloop-demo`.

## Seeded journeys

Delete `backend/careloop.db` and start the API once. The seed adds Mercy Demo (enrolled, SMS and band consent), Demo Awuor (home check), Demo Adhiambo (red label, band BAND-0012), Demo Nafula (navigating, voucher requested, cover unknown), Demo Kerubo (visit booked), and Demo Chemutai (postnatal watch). Hub HUB-0007 uses the device key `synthetic-device-key`.

Restarting does not reseed. An existing database from before this branch will not show Grace until that file is deleted.
