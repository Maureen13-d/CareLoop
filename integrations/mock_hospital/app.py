"""Mock hospital system (SIMULATED, synthetic data only).

A tiny FHIR R4 style server that pretends to be a hospital. It is NOT a real
hospital system and is not connected to any real one.

What it does:
  1. Receives an Appointment from CareLoop       POST /fhir/Appointment
  2. Rejects bad messages with an OperationOutcome (clear error)
  3. Lets us pretend the patient arrived and care moved on
                                                 POST /demo/advance/{id}
  4. Gives milestones back as FHIR Task resources
                                                 GET  /fhir/Task?based-on=Appointment/{id}

Run (from repo root, with the backend venv active):
    uvicorn integrations.mock_hospital.app:app --port 8100
"""
from itertools import count

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="Mock hospital (simulated)", version="0.1.0")

# in-memory "database": reset every time the process restarts
APPOINTMENTS: dict[str, dict] = {}
TASKS: dict[str, list[dict]] = {}
_ids = count(1)

# the coarse milestones CareLoop watches, in order
MILESTONES = ["arrived", "assessment-completed", "care-started"]
FHIR_JSON = "application/fhir+json"


def outcome(status: int, code: str, message: str) -> JSONResponse:
    """FHIR OperationOutcome = the standard way to say what went wrong."""
    body = {
        "resourceType": "OperationOutcome",
        "issue": [{"severity": "error", "code": code, "diagnostics": message}],
    }
    return JSONResponse(body, status_code=status, media_type=FHIR_JSON)


def validate_appointment(res: dict) -> str | None:
    """Return an error message, or None if the Appointment is acceptable."""
    if not isinstance(res, dict):
        return "Body must be a JSON object"
    if res.get("resourceType") != "Appointment":
        return "resourceType must be 'Appointment'"
    if res.get("status") not in ("proposed", "pending", "booked"):
        return "status must be one of: proposed, pending, booked"
    if not res.get("start"):
        return "start (date-time) is required"
    participants = res.get("participant")
    if not participants or not isinstance(participants, list):
        return "participant is required (patient and location)"
    refs = [p.get("actor", {}).get("reference", "") for p in participants]
    if not any(r.startswith("Patient/") for r in refs):
        return "participant must include a Patient/<id> reference"
    if not any(r.startswith("Location/") for r in refs):
        return "participant must include a Location/<id> reference"
    return None


def make_task(appt_id: str, milestone: str) -> dict:
    return {
        "resourceType": "Task",
        "id": f"task-{appt_id}-{milestone}",
        "status": "completed",
        "intent": "order",
        "basedOn": [{"reference": f"Appointment/{appt_id}"}],
        "code": {"coding": [{"system": "https://careloop.example/milestones", "code": milestone}]},
    }


@app.get("/health")
def health():
    return {"status": "ok", "service": "mock-hospital", "simulated": True}


@app.post("/fhir/Appointment")
async def receive_appointment(request: Request):
    try:
        res = await request.json()
    except Exception:
        return outcome(400, "structure", "Body is not valid JSON")
    error = validate_appointment(res)
    if error:
        return outcome(422, "invalid", error)
    appt_id = str(next(_ids))
    stored = {**res, "id": appt_id, "status": "booked"}  # the clinic "confirms"
    APPOINTMENTS[appt_id] = stored
    TASKS[appt_id] = []
    return JSONResponse(stored, status_code=201, media_type=FHIR_JSON,
                        headers={"Location": f"/fhir/Appointment/{appt_id}"})


@app.get("/fhir/Appointment/{appt_id}")
def get_appointment(appt_id: str):
    if appt_id not in APPOINTMENTS:
        return outcome(404, "not-found", f"Appointment/{appt_id} not found")
    return JSONResponse(APPOINTMENTS[appt_id], media_type=FHIR_JSON)


@app.post("/demo/advance/{appt_id}")
def advance(appt_id: str):
    """DEMO ONLY: move the pretend patient to the next hospital milestone."""
    if appt_id not in APPOINTMENTS:
        return outcome(404, "not-found", f"Appointment/{appt_id} not found")
    done = len(TASKS[appt_id])
    if done >= len(MILESTONES):
        return outcome(409, "conflict", "All milestones already reached")
    milestone = MILESTONES[done]
    TASKS[appt_id].append(make_task(appt_id, milestone))
    if milestone == "arrived":
        APPOINTMENTS[appt_id]["status"] = "fulfilled"
    return {"advanced_to": milestone}


@app.get("/fhir/Task")
def search_tasks(request: Request):
    """Milestones as a FHIR searchset Bundle. Use ?based-on=Appointment/<id>"""
    ref = request.query_params.get("based-on", "")
    if not ref.startswith("Appointment/"):
        return outcome(400, "required", "query parameter based-on=Appointment/<id> is required")
    appt_id = ref.split("/", 1)[1]
    tasks = TASKS.get(appt_id, [])
    bundle = {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(tasks),
        "entry": [{"resource": t} for t in tasks],
    }
    return JSONResponse(bundle, media_type=FHIR_JSON)
