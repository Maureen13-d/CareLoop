"""The only function that reads a contact. Dashboards and audit must not call it."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.followup.models import ContactVault


def contact_for_send(db: Session, public_id: str) -> str | None:
    row = db.scalar(select(ContactVault).where(ContactVault.public_id == public_id))
    return row.contact_ref if row else None
