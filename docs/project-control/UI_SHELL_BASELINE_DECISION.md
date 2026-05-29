# UI Shell Baseline Decision

Date: 2026-05-29

## Decision

`9d4edf3` is the user actually opened and accepted packaged preview UI identity.

`codex/integration-labtools-ui-c2-carryover` is the main UI page recovery reference line for Bioinformatics, Meta Analysis, and LabTools feature pages.

`e13d0f5f5dfda36a5c60a00ddc7820748fa1677f` is the carryover line HEAD recorded by `docs/ui/UI线路既往检查.md` and is an ancestor of `9d4edf3`.

`9d4edf3` is the later packaged preview identity on `codex/integration-labtools-ui-c2-carryover`.

`e13d0f5..9d4edf3` is limited to release UI gate button behavior, Settings detect-first behavior, and related UI tests.

Neither `9d4edf3` nor `e13d0f5f5dfda36a5c60a00ddc7820748fa1677f` may be merged wholesale into MainLine.

Current strategy: use `9d4edf3` as the accepted UI Shell / packaged preview baseline, keep `codex/integration-labtools-ui-c2-carryover` as the main UI page recovery reference line, and govern Shell baseline and feature page recovery separately.

## Source Preview

| Item | Value |
| --- | --- |
| Accepted preview bundle | `/Users/changdali/Developer/biomedpilot v1.0/Integration/dist/BioMedPilot Integration Preview.app` |
| `git_head` | `9d4edf3` |
| `launch_mode` | `packaged-local-python` |
| Historical recovery document | `docs/ui/UI线路既往检查.md` |
| Main recovery reference line | `codex/integration-labtools-ui-c2-carryover` |
| Historical check recorded HEAD | `e13d0f5f5dfda36a5c60a00ddc7820748fa1677f` |

## Baseline Separation

| Area | Governance Decision | MainLine Rule |
| --- | --- | --- |
| UI Shell | `9d4edf3` is the accepted UI Shell / packaged preview baseline. | Scoped Shell plan required; no whole-branch merge. |
| Bioinformatics pages | Recovery reference is `codex/integration-labtools-ui-c2-carryover`. | Route-by-route recovery plan required. |
| Meta Analysis pages | Recovery reference is `codex/integration-labtools-ui-c2-carryover`. | Route-by-route recovery plan required. |
| LabTools pages | Recovery reference is `codex/integration-labtools-ui-c2-carryover`, but preview pages may be old. | Page style audit required before migration. |
| Runtime/service | Not proven by Shell or historical UI page presence. | Runtime and tests required separately. |

## Explicit Non-Decisions

- This document does not authorize migration.
- This document does not authorize merge.
- This document does not authorize cherry-pick.
- This document does not authorize whole-branch use of `9d4edf3` or `e13d0f5f5dfda36a5c60a00ddc7820748fa1677f`.
- This document does not mark any feature page as MainLine migrated.
- Any UI page recovery still requires scoped route/page/runtime/test audit.

## Required Next Audits

| Audit | Output |
| --- | --- |
| `9d4edf3` to `e13d0f5` provenance check | Completed: `e13d0f5f5dfda36a5c60a00ddc7820748fa1677f` is an ancestor of `9d4edf3`; `9d4edf3` is the later packaged preview identity. |
| UI route inventory | Fill route-level handler, target page, runtime, test, and page style status. |
| LabTools page reconciliation | Classify each LabTools page as `figma/new`, `old`, `hybrid`, `placeholder`, or `missing`. |
| MainLine migration planning | Produce scoped migration entries before any code movement. |
