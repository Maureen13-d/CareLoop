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
