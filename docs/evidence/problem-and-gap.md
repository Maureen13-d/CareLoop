# Problem and Gap Evidence

Labels: **[V]** verified in the source listed, **[A]** assumption to validate, **[?]** not found. Sources were read during project research in November 2026; check the original papers before quoting numbers in a submission.

## Problem

| Claim | Status | Source |
|---|---|---|
| Kenya records roughly 5,845 new cervical cancer cases and 3,591 deaths a year (GLOBOCAN 2022, as reported) | [V] secondary report | https://peopledaily.digital/news/kenya-records-over-5k-new-cervical-cancer-cases-over-3k-deaths-annually |
| A western Kenya programme lost 31.5% overall, 27.9% after a positive VIA and 49.3% between biopsy and LEEP (2013) | [V] one programme, older data | https://ouci.dntb.gov.ua/works/4VR8goX4 |
| 39% of 100 VIA-positive women in two western Kenya hospitals defaulted from scheduled follow-up (2018) | [V] small sample | https://zendy.io/title/10.1200/jgo.18.41300 |
| HIV status and revisits were associated with higher loss to follow-up | [V] | https://ecommons.aku.edu/eastafrica_fhs_mc_obstet_gynaecol/686 |
| Barriers include transport, stigma and lack of social support; 20 to 40% loss after positive cytology is reported in many settings | [V] | https://pmc.ncbi.nlm.nih.gov/articles/PMC9847557 |
| A current national patient-level loss-to-follow-up figure | [?] | not found |

Do not present any single percentage as "Kenya's loss rate".

## Policy context

| Claim | Status | Source |
|---|---|---|
| Kenya launched a National Cervical Cancer Elimination Action Plan 2026 to 2030 on 15 January 2026, aligned to WHO targets, with referral strengthening and digital tools | [V] news report | https://www.standardmedia.co.ke/health/health-science/article/2001538723/state-rolls-out-five-year-plan-to-fight-cervical-cancer |
| WHO 90-70-90 includes 90% of those diagnosed receiving timely treatment | [V] news report | https://peopledaily.digital/news/kenya-records-over-5k-new-cervical-cancer-cases-over-3k-deaths-annually |
| National guidance recommends screening ages 25 to 49, HPV primary above 30 where available | [V] opinion piece; confirm against the guideline | https://www.standardmedia.co.ke/health/health-opinion/article/2001553796/hpv-vaccination-protecting-girls-today-from-cervical-cancer-tomorrow |

## Existing systems

| System | What sources show | Status | Source |
|---|---|---|---|
| KHIS (DHIS2) | Screening and treatment data are aggregated from registers into KHIS | [V] | https://pmc.ncbi.nlm.nih.gov/articles/PMC11249718/table/T5 ; https://search.r-project.org/CRAN/packages/cancerscreening/readme/README.html |
| KenyaEMR cancer screening module | One form with History, Symptoms, Screening and Follow up sections, plus MoH 745 and register reports | [V] | https://kenyahmis.org/wp-content/uploads/2023/07/KenyaEMR-Cervical-Cancer-Screening-_JobAid_July-2023_Final.pdf |
| Digital Health Act 2023 | In force from 2 November 2023 | [V] | https://new.kenyalaw.org/akn/ke/act/2023/15/eng@2023-11-24 |
| Digital Health Data Exchange Regulations | Describe a client registry, facility registry, health worker registry, interoperability layer and shared health records | [V] draft or gazetted text; confirm status | https://libraryir.parliament.go.ke/bitstreams/44501bea-fdae-417d-a5a2-db607a1f11fb/download |
| FHIR in Kenya | FHIR is policy-mandated with no fixed deadline; DHA publishes implementation guides such as Patient Summary | [V] | https://packages.fhir.org/jurisdictions/KE ; https://build.fhir.org/ig/IntelliSOFT-Consulting/Kenya-Patient-Summary-FHIR-IG |
| Afya Yangu | Reported as operational in 17 counties with portable patient data | [V] one news source, date unclear; **no integration verified** | https://www.talkafrica.co.ke/?p=35314 |
| CATSystem | Web-based cancer tracking system with algorithm-driven alerts, evaluated in a randomised trial | [V] closest prior art | https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11835318/ ; https://clinicaltrials.gov/study/NCT06286462 |

## Gap assessment

- **Supported [V]:** documented drop-off between positive screen and treatment; national reporting is largely aggregate.
- **Not verified [A]:** that routine hospital workflows lack cross-department closed-loop tracking with named owners and deadlines. Plausible, but no source describes routine practice at a specific hospital. Validate with short interviews.
- **Positioning:** CATSystem shows tracking is being tested. CareLoop's intended differences (open source, FHIR-shaped, explicit cross-department ownership and escalation, human-governed AI drafting) must be confirmed against the full protocol before being claimed.

## Next validation steps

1. Read the full CATSystem protocol and list its features.
2. Read the national cervical screening guideline for pathway steps and time windows.
3. Interview two or three people who work in the pathway (screener, gynaecology clinic nurse, records officer).
