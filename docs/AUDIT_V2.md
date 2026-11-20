# Audit v2: screening-to-care gap

Date: 20 Nov 2026. Branch base: `feat/careloop-maternal` at `94f17cf`.
This audit does not change behaviour. Maternal and hardware code is listed only.

The active product is follow-up after screening: a person is screened, a result needs a visit, and nobody is responsible for seeing that they arrive. CareLoop should follow each consenting person until arrival, and tell a community health worker who to chase and what to do.

An earlier maternal-and-hardware plan is not the plan for this branch. That code stays in the tree, untouched, so it can be decided later.

The channel named in an earlier draft as WhatsApp is Telegram here, plus a simulator, because the demo must run without a WhatsApp Business account. No Docker.

All data in this repository is synthetic.

## Feature gap table

| ID | Title | Status | What already exists | What is missing |
|---|---|---|---|---|
| F02 | Screening registration and patient ID | Partial | Clinician records a cervical screening and may open a case: `backend/app/modules/screenings/`, `frontend/src/app/(app)/intake/`. Patient ref is a sequential `CL-######` in `backend/app/modules/patients/service.py`. | Generic finding (concerning / urgent / not concerning / inadequate), language, channel (Telegram / SMS / USSD / web), consent, a non-sequential ID with a check digit, and a printable slip (ID, QR of the ID only, three plain lines, no condition, no contact). |
| F03 | Secure patient access | Missing | Staff login is username and password: `backend/app/modules/auth/`. | ID plus a simulated one-time code, expiry, single use, rate limit and lockout, identical errors for unknown and wrong IDs, expiring patient sessions. |
| F04 | Pseudonymisation split | Missing | Patients are pseudonymous refs, but there is no separate contact vault. Audit can store structured labels: `backend/app/modules/audit/`. | A `contact_vault` keyed by the public ID, one narrow send function, and an honest note that an ID plus a contact is still personal data. |
| F05 | Journey model | Partial | Pathway engine: `backend/app/modules/pathways/loader.py`, `service.py`. Cervical file `pathways/cervical_cancer.yaml`. Maternal file `pathways/maternal.yaml` (leave it). Endings and assumed deadlines already load from YAML. Arrival on the cervical pathway is a clinician role. | One generic follow-up pathway with states `screened` through `with_hospital`, endings `closed`, `chose_to_stop`, `closed_by_person`, and a validator test. Do not remove the cervical file. Cervical analytics must keep ignoring other pathways. |
| F06 | Facility dashboard | Partial | Cervical funnel and open-case counts: `backend/app/modules/analytics/router.py`, `frontend/src/app/(app)/desk/`. Maternal desk is separate. | Funnel on the new states, median and distribution of time from screening to arrival, percent arrived, aging list by ID, per-patient timeline without private text, and a lost-to-follow-up queue only a human can act on. |
| F07 | CHW worklist | Partial | Maternal CHW home lists assigned pregnancies and shows names: `backend/app/modules/maternal/service.py` `list_pregnancies`, `frontend/src/app/(app)/chw/`. CHW role exists (`grace`). | A ranked worklist of assigned follow-up patients: ID, days, state, reason label, recommended action, one-tap claim / attempt / escalate / outcome, counts, ranking config. A worsening flag ranks first. Escalation creates one task. A CHW must not see another CHW's patients. Do not change the maternal list. |
| F08 | Patient web portal | Partial | Cervical web chat: `frontend/src/app/(app)/chat/`. Phone lab: `frontend/src/app/(app)/phone/`. | ID plus second check, English or Swahili, plain "your next step", barrier help, confirm-first tasks, mobile layout. |
| F09 | Conversation core | Partial | Cervical assistant is one module (safety, then menus, then retrieval): `backend/app/modules/assistant/service.py`. Maternal companion is a second rule set, opt-in only. USSD and SMS menus live in `backend/app/modules/channels/service.py`. Banned words live in lite templates and `backend/app/modules/maternal/triage.py` `BANNED_SMS`. | One follow-up core used by web, Telegram, USSD, and the avatar. No channel-specific copy of the rules. English and Swahili in config. SMS 160 ASCII, USSD 182. Audit stores labels, not patient text. Existing cervical and maternal menus stay. |
| F10 | Check-in scheduler | Partial | Demo clock: `backend/app/core/clock.py` and the admin advance route in `backend/app/modules/pathways/router.py`. Deadline sweep: `run_deadline_check`. SMS STOP/START: `backend/app/modules/channels/service.py`. | Every-other-day check-in before arrival, quiet hours, attempt cap, stop on STOP / arrival / closure, fixed questions, worse or unclear or silence opens one CHW task and never reassures. |
| F11 | Telegram adapter | Missing | No WhatsApp and no Telegram webhook. The phone lab simulates USSD and SMS only. | Webhook with signature check, messages normalised into the conversation core, free-form versus template dispatcher logged by label, simulator page, credentials only in environment variables. Purpose-built rules, not an open assistant. |
| F12 | USSD contract | Partial | Working USSD simulator and session model: `backend/app/modules/channels/`. | A provider-neutral contract in `docs/USSD_CONTRACT.md` and tests with mocked inputs. No Africa's Talking client. |
| F13 | Avatar guide | Missing | No character, no speech. | Web-only guide that speaks the core reply exactly, with captions, mute, reduced motion, and a calm danger screen. |
| F14 | Safety checklist | Partial | Cervical safety tests: `backend/tests/test_assistant_safety.py`. Maternal triage tests: `backend/tests/test_maternal_triage.py`. Discreet SMS tests in `backend/tests/test_workspace.py`. | The ten follow-up checks (danger task, no enumeration, no duplicate tasks, STOP/START, discreet outbound, audit without patient text, overdue on the worklist, human arrival and human lost-to-follow-up, avatar text equals core text, unclear input escalates). Clinical wording marked pending review. Do not retune the cervical or maternal lexicons. |
| F15 | Metrics and fairness | Partial | Cervical outreach metrics and an honest, poor cervical eval. Maternal held-out scores are frozen in `docs/EVALUATION.md` and `backend/tests/test_maternal_eval.py`. | A synthetic cohort of at least 200 follow-up journeys, sliced by language, channel, and area, with an explicit non-causal caveat, plus a held-out danger-sign set that is not used to tune the lexicon. |
| F16 | Submission docs | Partial | `README.md`, `docs/ARCHITECTURE.md`, `docs/EVALUATION.md`, `docs/DEMO_SCRIPT.md` (maternal story), `docs/SECURITY_AND_PRIVACY.md`, `docs/DATA_POLICY.md`. | `docs/SUBMISSION.md`, screening architecture diagram, `docs/DATA_GOVERNANCE.md`, `docs/DATA_DECLARATION.md`, `docs/LIMITATIONS.md`, a screening demo script that does not erase the maternal script, `docs/HARDWARE_NEXT.md` (documentation only). |

## Maternal and hardware code (unchanged)

Leave all of these as they are:

- `pathways/maternal.yaml`
- `rules/maternal_triage.yaml`, `rules/band_nudges.yaml`, `rules/parity_fixture.json`
- `backend/app/modules/maternal/` (journey, triage, devices, companion, desk, eval)
- `backend/app/modules/channels/service.py` maternal `M` / `CHECK` prefixes
- `backend/app/modules/assistant/service.py` maternal early return
- `backend/app/modules/interop/service.py` antenatal milestone branch
- `integrations/mock_hospital/app.py` antenatal track
- `ai/lexicon/maternal_signs.yaml`, `ai/templates/maternal.yaml`, `ai/knowledge/passages_maternal.yaml`
- `ai/eval/maternal_dev.jsonl`, `ai/eval/maternal_test.jsonl`
- `frontend/src/app/(app)/chw/`, `frontend/src/app/(app)/hub/`, `frontend/src/lib/maternalTriage.mjs`
- `frontend/src/app/(app)/desk/[id]/MaternalPanel.tsx`
- `docs/MATERNAL.md`, `docs/HARDWARE.md`, `docs/DEVICE_API.md`, maternal section of `docs/EVALUATION.md`, maternal demo in `docs/DEMO_SCRIPT.md`
- Seeded CHW `grace` and the six synthetic pregnancies in `backend/app/workspace_seed.py`

The pathway engine change that limits the maternal CHW assignment check to `pathway_id == "maternal"` is a compatibility fix so a follow-up CHW can move follow-up cases. Maternal cases still go through `assert_chw_assignment`.

## Roles already in the seed

Password for every demo account is `careloop-demo`.

| Username | Role |
|---|---|
| amina | navigator |
| david | clinician (this is the screener; no new role) |
| aisha | patient |
| wanjiku | counsellor |
| peter | program manager |
| admin | admin |
| grace | CHW (maternal assignments stay hers) |

A follow-up demo will add synthetic assigned journeys for a CHW. Grace keeps her maternal women. New journeys use IDs, not names, on the new screens.

## Test status

Command (does not touch `backend/careloop.db`; tests force an in-memory database):

`backend\.venv\Scripts\python.exe -m pytest -q --tb=line`

Result on `94f17cf` before follow-up code: **254 passed**. Failures: none. Warnings are the known insecure demo JWT key and library deprecations. They are not fixed here.

`npx tsc --noEmit` in `frontend` was clean on that same commit.

## Proposed order

P0, in this order, because later features sit on earlier ones:

1. F01 hygiene (ignore rules, env example, one test command).
2. F05 generic pathway file and validator. Cervical and maternal files stay.
3. F02 registration, public ID, slip. Contacts go straight into the vault table.
4. F03 one-time code, lockout, no enumeration.
5. F09 conversation core (Telegram, web, and USSD will call it).
6. F14 the ten safety tests, so later features cannot break them.
7. F07 CHW worklist.
8. F06 facility dashboard.
9. Tag `p0-complete` and push.

Then P1: F04 governance note (the vault table arrives with F02), F10 check-ins, F08 portal, F11 Telegram simulator, F15 cohort, F16 docs.

Then P2: F12 USSD contract only, F13 avatar, F17 full run and `submission-ready`.

If time runs out, P0 is finished and pushed before P1 starts.

## Decisions recorded

- Screener is the existing clinician role.
- Telegram replaces WhatsApp. The 24-hour window is still implemented as a free-form versus template dispatcher and logged by label.
- Maternal code is not extended and not deleted.
- A local stash named `wip before maternal branch` (warm-paper UI) is still unapplied and is not part of this work.
