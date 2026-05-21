# Medical Terms Candidate Archive Policy

Date: 2026-05-20

## Policy

Review batches and candidate pools must be lifecycle-managed so closed batches are not mistaken for active runtime candidates.

## States

- `active`: current pending review queue.
- `closed`: reviewed batch with a decision report.
- `archive`: historical rows retained for traceability and excluded from runtime build scripts.
- `evidence_only`: evidence retained but not runtime-eligible.
- `future_scope`: out-of-current-scope candidates.
- `candidate_only`: explicitly not current runtime seed.

## Rules

- Active queues should contain only current pending batches.
- Processed batches must be marked closed in summary or decision reports.
- Candidate-only and future-scope pools should be periodically archived.
- Source evidence and manual decisions must not be deleted.
- Runtime build scripts must not read archive files.
- Archive entries must track source batch and decision report.
