import asyncio
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.db import init_db
from app.core.errors import register_error_handlers
from app.modules.assistant.router import router as assistant_router
from app.modules.audit.router import router as audit_router
from app.modules.auth.router import router as auth_router
from app.modules.pathways.router import admin_router, escalation_router, pathway_router
from app.modules.pathways.router import router as cases_router
from app.modules.pathways.scheduler import scheduler_loop
from app.modules.patients.router import router as patients_router
from app.modules.screenings.router import router as screenings_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
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
def health():
    return {"status": "ok", "synthetic_data_only": True}


for module_router in (auth_router, patients_router, screenings_router, cases_router, escalation_router,
                      pathway_router, assistant_router, audit_router, admin_router):
    api.include_router(module_router)

app.include_router(api)
