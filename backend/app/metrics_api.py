from fastapi import APIRouter, Depends

from app.deps import get_repo
from app.metrics import Metrics, compute_metrics
from app.repository import Repository

router = APIRouter(tags=["metrics"])


@router.get("/metrics", response_model=Metrics)
def get_metrics(repo: Repository = Depends(get_repo)):
    return compute_metrics(repo.list_cases(), repo.load_log())
