from fastapi import APIRouter, HTTPException, Query
from app.services.ingestion import load_sources
from app.services.reconciliation import reconcile

router = APIRouter(prefix="/api", tags=["meetings"])

def get_meetings():
    calendar, crm = load_sources()
    return reconcile(calendar, crm)

@router.get("/meetings")
def list_meetings(status: str | None = None, q: str | None = None, date_from: str | None = None, date_to: str | None = None):
    meetings = get_meetings()
    if status:
        meetings = [m for m in meetings if m["reconciliation_status"] == status]
    if q:
        needle = q.casefold()
        meetings = [m for m in meetings if needle in str(m).casefold()]
    if date_from:
        meetings = [m for m in meetings if m["meeting_date"] and m["meeting_date"] >= date_from]
    if date_to:
        meetings = [m for m in meetings if m["meeting_date"] and m["meeting_date"] <= date_to]
    return {"count": len(meetings), "items": meetings}

@router.get("/meetings/{meeting_id}")
def meeting_detail(meeting_id: str):
    for meeting in get_meetings():
        if meeting["meeting_id"] == meeting_id:
            return meeting
    raise HTTPException(status_code=404, detail="Meeting not found")

@router.get("/conflicts")
def list_conflicts():
    meetings = get_meetings()
    return {"count": sum(len(m["conflicts"]) for m in meetings),
            "items": [m for m in meetings if m["conflicts"] or m["duplicate_candidate"]]}

@router.post("/sync")
def sync():
    calendar, crm = load_sources()
    items = reconcile(calendar, crm)
    return {"message":"Sync completed", "calendar_records":len(calendar), "crm_records":len(crm),
            "unified_meetings":len(items), "conflicts":sum(len(x["conflicts"]) for x in items)}
