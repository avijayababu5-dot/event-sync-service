# AI Collaboration / Development Notes

## Prompting and planning
AI assistance was used to:
- translate the assessment into ingestion, normalization, matching, conflict, API, and UI workstreams;
- identify sample-data edge cases: malformed date, malformed email, missing time/location, time-zone ambiguity, status disagreement, source-only records, and possible same-source duplicates;
- propose a source-preserving canonical meeting representation;
- draft FastAPI endpoints, Vue UI components, tests, and README structure.

## Human review decisions
- Do not overwrite CRM values with Calendar values or vice versa.
- Do not auto-delete possible duplicates.
- Treat time differences as potential timezone/source discrepancies, not automatic proof of distinct meetings.
- Keep single-source records in the unified result.
- Make match confidence and reasons visible to aid review.

## Known limitations
- The current reconciliation engine uses deterministic heuristics and a small set of company-specific evidence patterns derived from the supplied sample.
- It is a take-home implementation, not a production-grade entity-resolution platform.
- Meeting IDs are generated per reconciliation run; stable IDs should be persisted in a database in a production version.
- Timezone-naive values cannot safely be compared to UTC timestamps without source timezone metadata.
- The demo currently loads JSON files on each request rather than persisting an ingestion snapshot.

## Suggested next improvements
1. Add Pydantic source models and a rejected-record report.
2. Persist normalized records and reconciliation decisions in PostgreSQL.
3. Add a human review workflow for low-confidence candidate pairs.
4. Introduce configurable source precedence only for fields where the business explicitly defines authority.
5. Add audit logs and metrics for match rate, conflict rate, and ingestion failures.
