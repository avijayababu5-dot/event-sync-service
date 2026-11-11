# Event Sync Service

A full-stack assessment implementation that ingests CRM and Calendar JSON records, reconciles likely matches, preserves source provenance, and exposes conflicts through a REST API and Vue interface.

## Stack
- Backend: Python 3.11+, FastAPI, Pydantic, dateutil
- Frontend: Vue 3, TypeScript, Vite, Axios
- Tests: pytest, FastAPI/httpx-compatible test dependencies

## Quick start

### 1. Backend
```bash
cd backend
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
API: http://localhost:8000  
Swagger: http://localhost:8000/docs

### 2. Frontend (new terminal)
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173.

### 3. One-command start
From repository root:
- Windows: run `start.bat`
- macOS/Linux: `bash start.sh`

The scripts install dependencies on first run if needed and start both dev servers in separate processes. For predictable environments, the manual steps above are recommended.

## API
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/api/meetings` | Unified meetings; supports `q`, `status`, `date_from`, `date_to` |
| GET | `/api/meetings/{meeting_id}` | One meeting |
| GET | `/api/conflicts` | Meetings with field conflicts or duplicate candidates |
| POST | `/api/sync` | Re-run ingestion and reconciliation |

## Reconciliation approach and decisions

1. **Ingest:** load both JSON arrays from `backend/data/`.
2. **Normalize:** parse ISO timestamps and common date formats; the supplied `03-15/2025` CRM date is explicitly normalized. Email addresses are case-folded and `[at]` is normalized to `@` for matching evidence.
3. **Cross-source matching:** candidate score uses same date (0.30), client/company evidence (0.40), relationship owner/organizer (0.10), and close meeting time (up to 0.20). A score of 0.65 or above is accepted. Time differences larger than 90 minutes do not automatically reject a candidate because source timezone conventions may differ; they are surfaced as a possible time conflict.
4. **One-to-one assignment:** a Calendar event can match at most one CRM record, and a CRM record can be consumed at most once. Candidate ranking is deterministic for a given input order.
5. **Unmatched retention:** records found in only one source remain in the unified list with `calendar_only` or `crm_only` status.
6. **Conflict handling:** values from both systems are retained in `calendar` and `crm` objects. The API never silently overwrites one source's value. Conflicts are explicitly listed.
7. **Duplicate candidates:** overlapping Calendar events with substantial attendee overlap and start times within 90 minutes are marked for review. They are not automatically merged or deleted.
8. **Status disagreements:** source status values are preserved and surfaced when different. Business status semantics are not assumed to be identical across systems.

### Matching limitations / production considerations
The source data has no shared meeting identifier and some records have ambiguous or timezone-naive timestamps. The score is a transparent heuristic, not proof of identity. In production, I would add:
- explicit source timezone configuration and UTC normalization;
- persistent source snapshots and idempotent upserts keyed by `(source, source_id)`;
- a review queue for ambiguous matches and duplicate candidates;
- calibrated matching thresholds with labeled historical pairs;
- audit history for human-approved merges and overrides;
- schema validation/dead-letter handling for malformed source records;
- database-backed persistence and scheduled/incremental sync.

The provided implementation intentionally favors explainability and preserving evidence over destructive merging.

## Data files
The assessment sample datasets are included in `backend/data/`. Replace these files with the complete upstream JSON exports when supplied; the loader expects top-level JSON arrays.

## Tests
```bash
cd backend
pytest -q
```

## AI assistance disclosure
AI assistance was used to brainstorm architecture, identify edge cases in the sample data, draft the initial implementation, and prepare documentation. The matching rules and assumptions are documented above and should be reviewed by the developer. No claim is made that heuristic matches are infallible; source records and conflicts remain visible for human verification.
