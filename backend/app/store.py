"""In-memory state. Replace with a database layer in a follow-up ticket."""

from app.models import Case
from app.outreach import OutreachEvent

STORE: dict[str, Case] = {}
OUTREACH_LOG: list[OutreachEvent] = []
