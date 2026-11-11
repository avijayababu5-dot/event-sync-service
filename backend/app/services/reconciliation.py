from difflib import SequenceMatcher
from uuid import uuid4
from .normalization import normalize_text, normalize_email, parse_date, parse_datetime, time_minutes

def _calendar_person_emails(event):
    return {e for e in (normalize_email(x) for x in event.get("attendees", [])) if e}

def _crm_person_email(crm):
    # Client email is not supplied by CRM; company/name are used as identity evidence.
    return None

def _company_from_calendar(event):
    text = " ".join([event.get("title") or "", event.get("description") or ""]).casefold()
    known = {
        "meridian capital": ["meridian", "david.park@meridiancap.com"],
        "summit advisors": ["summit", "summitadv.com"],
        "crestview holdings": ["crestview", "crestviewhold.com"],
        "pinnacle group": ["pinnacle", "pinnaclegp.com"],
        "atlas ventures": ["atlas", "atlasvc.com"],
        "horizon wealth partners": ["horizon", "horizonwp.com"],
        "granite point capital": ["granite", "granitepointcap.com"],
        "evergreen capital": ["evergreen", "evergreencap.com"],
        "redwood institutional": ["redwood", "redwoodinst.com"],
        "fund vii investors": ["fund vii closing dinner", "external-guests"],
    }
    for company, tokens in known.items():
        if any(t in text for t in tokens):
            return company
    return None

def _calendar_client_evidence(event):
    attendees = _calendar_person_emails(event)
    title = (event.get("title") or "").casefold()
    desc = (event.get("description") or "").casefold()
    evidence = " ".join([title, desc, " ".join(attendees)])
    return evidence

def _score(calendar, crm):
    score = 0.0
    reasons = []
    cdate = parse_datetime(calendar.get("start_time"))
    rdate = parse_date(crm.get("meeting_date"))
    if cdate and rdate and cdate.date() == rdate:
        score += 0.30; reasons.append("same calendar date")
    elif cdate and rdate:
        return 0.0, []

    company = (crm.get("client_company") or "").casefold()
    evidence = _calendar_client_evidence(calendar)
    if company and any(token in evidence for token in {
        "Meridian Capital": ["meridian", "meridiancap.com"],
        "Summit Advisors": ["summit", "summitadv.com"],
        "Crestview Holdings": ["crestview", "crestviewhold.com"],
        "Pinnacle Group": ["pinnacle", "pinnaclegp.com"],
        "Atlas Ventures": ["atlas", "atlasvc.com"],
        "Horizon Wealth Partners": ["horizon", "horizonwp.com"],
        "Granite Point Capital": ["granite", "granitepointcap.com"],
        "Evergreen Capital": ["evergreen", "evergreencap.com"],
        "Redwood Institutional": ["redwood", "redwoodinst.com"],
        "Fund VII Investors": ["fund vii closing dinner", "fund vii final close"],
    }.get(crm.get("client_company"), [company])):
        score += 0.40; reasons.append("client/company evidence")

    owner = (crm.get("relationship_owner") or "").casefold().replace(" ", ".")
    organizer = (calendar.get("organizer") or "").casefold()
    if owner and owner in organizer:
        score += 0.10; reasons.append("relationship owner matches organizer")

    ctime = cdate.hour * 60 + cdate.minute if cdate else None
    rtime = time_minutes(crm.get("meeting_time"))
    if ctime is not None and rtime is not None:
        delta = abs(ctime-rtime)
        if delta <= 15:
            score += 0.20; reasons.append("meeting times within 15 minutes")
        elif delta <= 90:
            score += 0.10; reasons.append("meeting times within 90 minutes")
        # Larger differences may be timezone-related; do not add points or reject.

    # Internal meetings have no client company. Require strong title similarity and same date.
    if not company and cdate and rdate:
        a = normalize_text(calendar.get("title")) or ""
        b = normalize_text(crm.get("subject")) or ""
        similarity = SequenceMatcher(None, a, b).ratio()
        if similarity >= 0.45:
            score += 0.30 * similarity; reasons.append("similar internal meeting title")
    return min(score, 1.0), reasons

def _field(value, source):
    return {"value": value, "source": source}

def _conflict(field, left, right):
    if left is None or right is None or not str(left).strip() or not str(right).strip():
        return None
    if normalize_text(left) == normalize_text(right):
        return None
    return {"field": field, "calendar_value": left, "crm_value": right}

def reconcile(calendar_events, crm_events, threshold=0.65):
    """Greedy one-to-one cross-source matching; preserves all unmatched records."""
    used_crm = set()
    meetings = []

    # Detect likely duplicates inside calendar source without merging away evidence.
    calendar_duplicate_ids = set()
    for i, first in enumerate(calendar_events):
        for second in calendar_events[i+1:]:
            if parse_date(first.get("start_time")) != parse_date(second.get("start_time")):
                continue
            emails1, emails2 = _calendar_person_emails(first), _calendar_person_emails(second)
            overlap = len(emails1 & emails2) / max(1, len(emails1 | emails2))
            t1, t2 = time_minutes(first.get("start_time")), time_minutes(second.get("start_time"))
            close = t1 is not None and t2 is not None and abs(t1-t2) <= 90
            if overlap >= 0.5 and close:
                calendar_duplicate_ids.update([first["event_id"], second["event_id"]])

    for cal in calendar_events:
        ranked = []
        for crm in crm_events:
            if crm["crm_id"] in used_crm:
                continue
            score, reasons = _score(cal, crm)
            if score >= threshold:
                ranked.append((score, crm, reasons))
        ranked.sort(key=lambda x: x[0], reverse=True)
        match = ranked[0] if ranked else None
        if match:
            score, crm, reasons = match
            used_crm.add(crm["crm_id"])
            conflicts = []
            for field, cval, rval in [
                ("location", cal.get("location"), crm.get("location")),
                ("status", cal.get("status"), crm.get("status")),
            ]:
                item = _conflict(field, cval, rval)
                if item: conflicts.append(item)
            cdt = parse_datetime(cal.get("start_time"))
            rdate = parse_date(crm.get("meeting_date"))
            rtime = time_minutes(crm.get("meeting_time"))
            if cdt and rdate == cdt.date() and rtime is not None and abs(cdt.hour*60+cdt.minute-rtime) > 15:
                conflicts.append({"field":"meeting_time","calendar_value":cal.get("start_time"),"crm_value":crm.get("meeting_time"),"note":"Potential timezone or source-time discrepancy; values preserved."})
            meeting = {
                "meeting_id": f"MEET-{uuid4().hex[:10].upper()}",
                "title": _field(cal.get("title") or crm.get("subject"), "calendar" if cal.get("title") else "crm"),
                "meeting_date": (cdt.date().isoformat() if cdt else rdate.isoformat() if rdate else None),
                "calendar": cal, "crm": crm,
                "sources": {"calendar_id":cal["event_id"],"crm_id":crm["crm_id"]},
                "match_confidence": round(score, 2),
                "match_reasons": reasons,
                "reconciliation_status": "matched_with_conflicts" if conflicts else "matched",
                "conflicts": conflicts,
                "duplicate_candidate": cal["event_id"] in calendar_duplicate_ids
            }
        else:
            cdt = parse_datetime(cal.get("start_time"))
            meeting = {
                "meeting_id": f"MEET-{uuid4().hex[:10].upper()}",
                "title": _field(cal.get("title"), "calendar"),
                "meeting_date": cdt.date().isoformat() if cdt else None,
                "calendar": cal, "crm": None,
                "sources": {"calendar_id":cal["event_id"],"crm_id":None},
                "match_confidence": 0.0, "match_reasons": [],
                "reconciliation_status": "calendar_only", "conflicts": [],
                "duplicate_candidate": cal["event_id"] in calendar_duplicate_ids
            }
        meetings.append(meeting)

    for crm in crm_events:
        if crm["crm_id"] not in used_crm:
            rdate = parse_date(crm.get("meeting_date"))
            meetings.append({
                "meeting_id": f"MEET-{uuid4().hex[:10].upper()}",
                "title": _field(crm.get("subject"), "crm"),
                "meeting_date": rdate.isoformat() if rdate else None,
                "calendar": None, "crm": crm,
                "sources": {"calendar_id":None,"crm_id":crm["crm_id"]},
                "match_confidence": 0.0, "match_reasons": [],
                "reconciliation_status": "crm_only", "conflicts": [],
                "duplicate_candidate": False
            })
    meetings.sort(key=lambda x: (x["meeting_date"] or "9999-99-99", x["title"]["value"] or ""))
    return meetings
