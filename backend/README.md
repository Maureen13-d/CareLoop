# CareLoop backend

Python, FastAPI, SQLAlchemy, SQLite. **Synthetic data only.**

## What exists today

- Login with roles: navigator, clinician, counsellor, patient (role defined, patient login comes later), program manager, admin
- Synthetic patients and consent records
- Screenings; a concerning result opens a tracked case (if the patient consented)
- The case engine, driven by `pathways/cervical_cancer.yaml` (version 0.2, pre-hospital bridge): stages, owners, deadlines, evidence-to-close, patient decline, lost-to-follow-up by human decision
- Escalations raised by a deadline checker, with a demo clock
- Audit log of every state change and refused action
- **The assistant (Tier 0 and Tier 1):** safety rules and Lite mode (keyword and phrase matching with approved replies and barrier flags). No model, no network. Reads the files in `../ai/`.
- 91 automated tests

Not built yet: onboarding flow, patient login, navigation tasks, appointments, reminders and the SMS outbox, the USSD and SMS channel adapters and simulator, grounded retrieval and knowledge base, the mock hospital and FHIR exchange, analytics, frontend.

## Run it (first time)

You need Python 3.10 or newer. Run these from the `backend` folder.

```bash
# 1. Create an isolated Python environment (one-time)
python -m venv .venv

# 2. Activate it (do this every time you open a new terminal)
source .venv/bin/activate          # Mac / Linux / Git Bash
.venv\Scripts\activate             # Windows PowerShell

# 3. Install the libraries (one-time)
pip install -r requirements.txt

# 4. Create the demo database with synthetic data
python ../database/seeds/seed_demo.py --reset

# 5. Start the API
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs. This is an interactive page for trying every endpoint.
Click **Authorize**, log in as `navigator` with password `careloop-demo`, then try `GET /api/v1/cases`.

Demo accounts (all synthetic): `navigator`, `clinician`, `counsellor`, `manager`, `admin`. Same password for all (set `DEMO_PASSWORD` to change it).

## Try the assistant

In `/docs`, open `POST /api/v1/assistant/message` and send:

```json
{ "channel": "sms", "text": "how much will it cost, i have no money" }
```

You get an approved reply, a barrier flag (marked *suggested* until a patient confirms it), and a suggested navigator task. Try `"i want to die"` to see the safety path: it hands over to a human and the reply still holds a `[VERIFIED HELPLINE]` placeholder that must be replaced before real use. Menu answers look like `{ "channel": "ussd", "menu_choice": "2", "menu_context": "worry_menu" }`.

## Show an escalation in seconds (demo clock)

1. Log in as `admin`.
2. `POST /api/v1/admin/advance-clock` with `{"hours": 72}`.
3. `POST /api/v1/admin/run-deadline-check`.
4. Log in as `navigator` and open `GET /api/v1/escalations`.

The demo clock resets when the server restarts.

## Run the tests

```bash
pytest
```

Tests use a temporary in-memory database. They never touch `careloop.db`.

## Reset the demo

```bash
python ../database/seeds/seed_demo.py --reset
```

## Settings

Copy `../.env.example` to `backend/.env` to change settings. Never commit `.env`.

## Code map

```
app/
  main.py                  start-up and routing
  core/                    settings, database, security, demo clock, shared errors
  modules/
    auth/                  users, roles, login
    patients/              patients and consent
    screenings/            screening results; opens cases
    pathways/              the case engine (service.py) and the YAML loader
    assistant/             safety rules and Lite mode (no database, no network)
    audit/                 append-only audit log
tests/                     pytest suites
```

Rule: a module reads and writes only its own tables. To use another module's data, call its `service` functions.

## Closing the loop
`POST /outreach/cases/{id}/respond` records that the patient attended: the case advances, the
outreach ladder restarts for the new stage, and a `response` event is logged. Stages with more than
one valid outcome (screened, diagnostic done) require an explicit `to_stage`; the API returns 422
otherwise. The endpoint accepts no free text by design (see DATA_POLICY.md).

`GET /outreach/cases/{id}` returns status (on_track / overdue / escalated / closed), next stages and
the outreach timeline. `GET /outreach/escalated` lists cases awaiting a coordinator. UI: `/cases/{id}`.

### Demo scenario
Set `CARELOOP_DEMO_SCENARIO=true` in `backend/.env` to seed `case-demo` (`SYN-9000`), a case that is
already escalated, so the loop-closure flow can be shown without waiting for real time to pass.

## Closing the loop
`POST /outreach/cases/{id}/respond` records that the patient attended: the case advances, the
outreach ladder restarts for the new stage, and a `response` event is logged. Stages with more than
one valid outcome (screened, diagnostic done) require an explicit `to_stage`; the API returns 422
otherwise. The endpoint accepts no free text by design (see DATA_POLICY.md).

`GET /outreach/cases/{id}` returns status (on_track / overdue / escalated / closed), next stages and
the outreach timeline. `GET /outreach/escalated` lists cases awaiting a coordinator. UI: `/cases/{id}`.

### Demo scenario
Set `CARELOOP_DEMO_SCENARIO=true` in `backend/.env` to seed `case-demo` (`SYN-9000`), a case that is
already escalated, so the loop-closure flow can be shown without waiting for real time to pass.
