from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.channels import service
from app.modules.channels.schemas import SmsIn, SmsOut, UssdIn, UssdOut

router = APIRouter(tags=["channels"])


def _sms(message) -> SmsOut:
    return SmsOut(
        id=message.id,
        phone_ref=message.phone_ref,
        direction=message.direction,
        body=message.body,
        status=message.status,
        created_at=message.created_at,
    )


@router.post("/channels/ussd", response_model=UssdOut)
def post_ussd(data: UssdIn, db: Session = Depends(get_db)):
    text = service.handle_ussd(db, data.session_id, data.phone_ref, data.text)
    return UssdOut(text=text, end_session=False)


@router.post("/channels/sms/inbound", response_model=SmsOut | None)
def post_sms(data: SmsIn, db: Session = Depends(get_db)):
    message = service.inbound_sms(db, data.phone_ref, data.text)
    return _sms(message) if message else None


@router.post("/channels/sms/{message_id}/undelivered", response_model=SmsOut)
def post_undelivered(message_id: int, db: Session = Depends(get_db)):
    return _sms(service.mark_undelivered(db, message_id))


@router.get("/sim/sms-outbox", response_model=list[SmsOut])
def get_outbox(
    phone_ref: str | None = None,
    limit: int = Query(40, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return [_sms(message) for message in service.list_messages(db, phone_ref, limit)]
