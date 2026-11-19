# CareLoop

Care-pathway tracking MVP to prevent patients from falling through the cracks between screening, diagnosis, and treatment.

> **Synthetic data only.** Do not commit or enter real patient records (PHI/PII). See `docs/DATA_POLICY.md`.

## Stack
- **Backend:** Python 3.12+, FastAPI, Pydantic (`backend/`)
- **Frontend:** Next.js, TypeScript, Tailwind CSS (`frontend/`)

## Local Setup

### Backend
- `cd backend`
- `python -m venv .venv && source .venv/Scripts/activate`
- `pip install -e ".[dev]"`
- `uvicorn app.main:app --reload`
- API docs run at `http://localhost:8000/docs`.

### Frontend
- `cd frontend`
- `cp ../.env.example .env.local`
- `npm install && npm run dev`
- Web dashboard runs at `http://localhost:3000`.

## Running Checks
- `cd backend && ruff check . && pytest -q tests/test_api.py tests/test_pathway.py`
- `cd frontend && npm run lint && npm run build`

## Outreach engine
Overdue cases move up an escalation ladder: SMS → phone call → community health worker visit →
care-coordinator hand-off. A 3-day cooldown prevents repeat contact, and the ladder resets when a
case advances stage. Messages are deliberately neutral and never name the condition.
Channels are **simulated**; real delivery would require real contact details, which
[DATA_POLICY.md](docs/DATA_POLICY.md) forbids. Ladder and cooldown values are placeholders pending review.

API: `GET /outreach/queue` (dry run), `POST /outreach/sweep`, `GET /outreach/events`,
`POST /outreach/cases/{id}/send`. UI: `/outreach`.
