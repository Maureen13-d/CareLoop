from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.modules.assistant import service
from app.modules.assistant.schemas import AssistantRequest, AssistantResponse
from app.modules.audit import service as audit

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/message", response_model=AssistantResponse)
def post_message(data: AssistantRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    response = service.handle_message(data)
    # The audit record keeps labels only. The patient's own words are never written to the audit log.
    audit.record(
        db, actor=user, action="assistant.message", entity_type="assistant",
        detail={
            "channel": data.channel, "tier": response.tier, "safety_level": response.safety.level,
            "flags": [f.flag for f in response.barrier_flags], "needs_human": response.needs_human,
            "template_id": response.template_id,
        },
    )
    db.commit()
    return response
