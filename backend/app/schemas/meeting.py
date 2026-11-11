from pydantic import BaseModel
from typing import Any

class MeetingResponse(BaseModel):
    meeting_id: str
    title: dict
    meeting_date: str | None
    calendar: dict | None
    crm: dict | None
    sources: dict
    match_confidence: float
    match_reasons: list[str]
    reconciliation_status: str
    conflicts: list[dict]
    duplicate_candidate: bool
