# Legacy Feature Triage

Date: 2026-05-29

Purpose: classify historical UI recovery lines from `docs/ui/UI线路既往检查.md` under Project Control Constitution v2.

## Classification Rules

| Level | Meaning | Handling |
| --- | --- | --- |
| A | Current target has it and tests pass | Keep |
| B | Old/side branch has it, current target lacks it, value is clear | Scoped migration candidate |
| C | Old/side branch has it, but depends on old architecture | Extract ideas only |
| D | Fake implementation or obsolete behavior | Archive, do not migrate |
| E | Unknown | Create audit task before migration |

## B-Class Candidates From Historical UI Check

These items are classified as B because old `dev/integration` lacks them, while `codex/integration-labtools-ui-c2-carryover` has recovered UI page lines with clear value.

| Legacy Item | Source Branch / Commit | Level | Current Target Gap | Direct Migration Allowed? | Reason | Required Next Action |
| --- | --- | --- | --- | --- | --- | --- |
| Bioinformatics gate shell | `codex/integration-labtools-ui-c2-carryover` / `08e9bd1` | B | old `dev/integration` missing recovered gate shell | no | Valuable route foundation; shared UI conflicts possible | scoped route recovery plan |
| Bioinformatics Project Home and Data Source | `codex/integration-labtools-ui-c2-carryover` / `900ba60` | B | old `dev/integration` missing recovered pages | no | Clear page recovery source | scoped route recovery plan |
| Bioinformatics Data Check & Preparation and Group & Design | `codex/integration-labtools-ui-c2-carryover` / `62739aa` | B | old `dev/integration` missing recovered pages | no | Clear page recovery source | scoped route recovery plan |
| Bioinformatics Analysis Tasks | `codex/integration-labtools-ui-c2-carryover` / `4061d72` | B | old `dev/integration` missing recovered page | no | Clear page recovery source | scoped route recovery plan |
| Bioinformatics Result & Report / Report Export | `codex/integration-labtools-ui-c2-carryover` / `2d5a560` | B | old `dev/integration` missing recovered pages | no | Clear page recovery source; export gates need runtime audit | scoped route recovery plan |
| Meta Project and Question pages | `codex/integration-labtools-ui-c2-carryover` / `bf6aaf8` | B | old `dev/integration` missing recovered pages | no | Clear page recovery source | scoped route recovery plan |
| Meta Search and Reference pages | `codex/integration-labtools-ui-c2-carryover` / `e551f44` | B | old `dev/integration` missing recovered pages | no | Clear page recovery source | scoped route recovery plan |
| Meta Screening / Extraction / ROB pages | `codex/integration-labtools-ui-c2-carryover` / `557b645` | B | old `dev/integration` missing recovered pages | no | Clear page recovery source | scoped route recovery plan |
| Meta Result / Report / Export gates | `codex/integration-labtools-ui-c2-carryover` / `6fe2295` | B | old `dev/integration` missing recovered pages | no | Clear page recovery source; export gates need artifact audit | scoped route recovery plan |
| LabTools navigation and P0 UI pages | `codex/integration-labtools-ui-c2-carryover` / `3bf79f4`, `ca006ee`, `f18b9a0`, `a33cffe`, `00f4ec6` | B | old `dev/integration` missing recovered pages | no | Valuable, but page style may be old/hybrid | LabTools reconciliation per page |
| LabTools storage/read/write interfaces | `codex/integration-labtools-ui-c2-carryover` / `edfa2a5`, `7afe07b`, `e64454b`, `b40cc8d` | B | old `dev/integration` missing recovered interfaces | no | Clear interface value; write paths require stricter tests | scoped adapter migration plan |
| Shared Workbench UI foundation | `codex/integration-labtools-ui-c2-carryover` / `82db716`, `d2c6c92`, `b691fe6`, `a731f8a`, `1d663a7`, `cb10694` | B | old `dev/integration` lacks required shared foundation | no | Required by page recovery but known conflict area | shared foundation conflict plan |

## Triage Notes

- B classification is not migration approval.
- B classification means the item is worth scoped recovery planning.
- Direct whole-branch migration from `codex/integration-labtools-ui-c2-carryover` remains prohibited.
- Direct cherry-pick of old UI commits remains high risk until shared UI conflicts are planned.
