# CareLoop backend

Python, FastAPI, SQLAlchemy, SQLite. **Synthetic data only.**

## What exists today

- Login with roles (coordinator, clinician, program manager, admin)
- Synthetic patients and consent records
- Screening results; a positive result opens a tracked case (if the patient consented)
- The case engine: stages from `pathways/cervical_cancer.yaml`, owners, deadlines, evidence-to-close rule
- Escalations raised by a deadline checker, with a demo clock
- Audit log of every state change and refused action
- 36 automated tests

Not built yet: referrals, tasks and appointments, notifications, analytics, risk score, assistant, FHIR mapping, frontend.

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
Click **Authorize**, log in as `coordinator` with password `careloop-demo`, then try `GET /api/v1/cases`.

Demo accounts (all synthetic): `coordinator`, `clinician`, `manager`, `admin`. Same password for all (set `DEMO_PASSWORD` to change it).

## Show an escalation in seconds (demo clock)

1. Log in as `admin`.
2. `POST /api/v1/admin/advance-clock` with `{"hours": 72}`.
3. `POST /api/v1/admin/run-deadline-check`.
4. Log in as `coordinator` and open `GET /api/v1/escalations`.

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
    audit/                 append-only audit log
tests/                     pytest suites
```

Rule: a module reads and writes only its own tables. To use another module's data, call its `service` functions.
