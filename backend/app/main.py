from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.fhir import case_to_fhir_task
from app.models import AdvanceRequest, Case, CaseView
from app.pathway import InvalidTransition, Stage, is_overdue
from app.synthetic import generate_cases

STORE: dict[str, Case] = {}


@asynccontextmanager
async def lifespan(_: FastAPI):
    STORE.clear()
    STORE.update({c.id: c for c in generate_cases(settings.seed_cases, settings.seed)})
    yield


app = FastAPI(title="CareLoop API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _view(case: Case) -> CaseView:
    return CaseView(
        **case.model_dump(), overdue=is_overdue(case.stage, case.stage_entered_at)
    )


def _get(case_id: str) -> Case:
    case = STORE.get(case_id)
    if case is None:
        raise HTTPException(404, "Case not found")
    return case


@app.get("/health")
def health():
    return {"status": "ok", "data": "synthetic-only"}


@app.get("/cases", response_model=list[CaseView])
def list_cases(stage: Stage | None = None, overdue: bool | None = None):
    views = [_view(c) for c in STORE.values()]
    if stage is not None:
        views = [v for v in views if v.stage == stage]
    if overdue is not None:
        views = [v for v in views if v.overdue == overdue]
    return views


@app.get("/cases/{case_id}", response_model=CaseView)
def get_case(case_id: str):
    return _view(_get(case_id))


@app.post("/cases/{case_id}/advance", response_model=CaseView)
def advance_case(case_id: str, body: AdvanceRequest):
    case = _get(case_id)
    try:
        case.advance(body.to_stage)
    except InvalidTransition as e:
        raise HTTPException(409, str(e)) from e
    return _view(case)


@app.get("/cases/{case_id}/fhir-task")
def get_fhir_task(case_id: str):
    return case_to_fhir_task(_get(case_id))
