# Emtree Mapping Review Plan

Date: 2026-05-20

## Current State

- Emtree rows: `190`
- Rows with `emtree_review_status=needs_review`: `190`
- Embase search enabled: `false`

## Rules

- Do not automatically guess Emtree terms.
- Keep `needs_review` when no reliable mapping exists.
- Prioritize disease, exposure, intervention, and outcome seed concepts.
- Every reviewed mapping must record source, reviewer, review status, and notes.
- Full Emtree completion is not required before Embase retrieval is designed and implemented.
