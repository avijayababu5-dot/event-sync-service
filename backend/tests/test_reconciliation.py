from app.services.reconciliation import reconcile
from app.services.normalization import parse_date, normalize_email

def test_malformed_date_is_normalized():
    assert parse_date("03-15/2025").isoformat() == "2025-03-15"

def test_invalid_email_is_normalized_safely():
    assert normalize_email("raj.patel[at]atlasvc.com") == "raj.patel@atlasvc.com"
    assert normalize_email("not-an-email") is None

def test_cross_source_match_and_unmatched_records():
    calendar = [{
        "event_id":"CAL-X","title":"Meridian Portfolio Review",
        "organizer":"sarah.chen@firma.com",
        "attendees":["david.park@meridiancap.com"],
        "start_time":"2025-03-10T14:00:00","end_time":"2025-03-10T15:00:00",
        "location":"Zoom","status":"confirmed"
    }]
    crm = [{
        "crm_id":"CRM-X","subject":"Portfolio Review","client_name":"David Park",
        "client_company":"Meridian Capital","relationship_owner":"Sarah Chen",
        "meeting_date":"2025-03-10","meeting_time":"14:00",
        "location":"Office","status":"Confirmed"
    }, {
        "crm_id":"CRM-Y","subject":"Unmatched","client_company":"Other Co",
        "relationship_owner":"Someone","meeting_date":"2025-03-11","meeting_time":"10:00"
    }]
    result = reconcile(calendar, crm)
    assert len(result) == 2
    matched = next(x for x in result if x["sources"]["crm_id"] == "CRM-X")
    assert matched["reconciliation_status"] == "matched_with_conflicts"
    assert any(c["field"] == "location" for c in matched["conflicts"])
    assert any(x["reconciliation_status"] == "crm_only" for x in result)

def test_calendar_only_is_retained():
    result = reconcile([{"event_id":"C","title":"Solo","start_time":"2025-01-01T10:00:00"}], [])
    assert result[0]["reconciliation_status"] == "calendar_only"
