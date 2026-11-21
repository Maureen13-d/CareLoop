import asyncio
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from app.core.config import settings
from app.core.db import SessionLocal, init_db
from app.core.errors import register_error_handlers
from app.db import engine as outreach_engine
from app.db import init_db as init_outreach_db
from app.deps import get_repo
from app.fhir import case_to_fhir_task
from app.metrics_api import router as metrics_router
from app.models import Case, CaseView
from app.modules.analytics.router import router as analytics_router
from app.modules.assistant.router import router as assistant_router
from app.modules.audit.router import router as audit_router
from app.modules.auth.router import router as auth_router
from app.modules.channels.router import router as channels_router
from app.modules.followup.router import router as followup_router
from app.modules.interop.router import router as hospital_router
from app.modules.ksl.research.router import router as ksl_research_router
from app.modules.ksl.router import router as ksl_router
from app.modules.maternal.device_router import router as device_router
from app.modules.maternal.router import router as maternal_router
from app.modules.pathways.router import admin_router, escalation_router, pathway_router
from app.modules.pathways.router import router as cases_router
from app.modules.pathways.scheduler import scheduler_loop
from app.modules.patients.router import router as patients_router
from app.modules.screenings.router import router as screenings_router
from app.modules.tasks.router import router as tasks_router
from app.outreach_api import router as outreach_router
from app.pathway import Stage, is_overdue
from app.repository import Repository
from app.seed import seed_if_empty
from app.workspace_seed import seed_workspace_if_empty


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    init_outreach_db()  # create outreach tables if missing; never drops anything
    with Session(outreach_engine) as session:
        seed_if_empty(session)  # first run only
    with SessionLocal() as session:
        seed_workspace_if_empty(session)
    task = None
    if settings.enable_scheduler:
        task = asyncio.create_task(scheduler_loop(settings.scheduler_interval_seconds))
    yield
    if task:
        task.cancel()


app = FastAPI(
    title="CareLoop API",
    version="0.1.0",
    description="Care-pathway orchestration layer. SYNTHETIC DATA ONLY. Not a medical device; no clinical validation.",
    lifespan=lifespan,
)
register_error_handlers(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = APIRouter(prefix="/api/v1")


@api.get("/health", tags=["system"])
def health_v1():
    return {"status": "ok", "synthetic_data_only": True}


for module_router in (
    auth_router,
    patients_router,
    screenings_router,
    cases_router,
    escalation_router,
    pathway_router,
    assistant_router,
    audit_router,
    admin_router,
    analytics_router,
    tasks_router,
    channels_router,
    hospital_router,
    maternal_router,
    device_router,
    followup_router,
    ksl_router,
    ksl_research_router,
):
    api.include_router(module_router)

app.include_router(api)
app.include_router(outreach_router)
app.include_router(metrics_router)


def _view(case: Case) -> CaseView:
    return CaseView(**case.model_dump(), overdue=is_overdue(case.stage, case.stage_entered_at))


def _get(repo: Repository, case_id: str) -> Case:
    case = repo.get_case(case_id)
    if case is None:
        raise HTTPException(404, "Case not found")
    return case


@app.get("/health")
def health():
    return {"status": "ok", "data": "synthetic-only"}


@app.get("/cases", response_model=list[CaseView])
def list_cases(
    stage: Stage | None = None,
    overdue: bool | None = None,
    repo: Repository = Depends(get_repo),
):
    views = [_view(c) for c in repo.list_cases()]
    if stage is not None:
        views = [v for v in views if v.stage == stage]
    if overdue is not None:
        views = [v for v in views if v.overdue == overdue]
    return views


@app.get("/cases/{case_id}", response_model=CaseView)
def get_case(case_id: str, repo: Repository = Depends(get_repo)):
    return _view(_get(repo, case_id))


@app.get("/cases/{case_id}/fhir-task")
def get_fhir_task(case_id: str, repo: Repository = Depends(get_repo)):
    return case_to_fhir_task(_get(repo, case_id))
