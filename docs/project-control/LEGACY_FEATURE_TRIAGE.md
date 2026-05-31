# Legacy Feature Triage

Date: 2026-05-29

Purpose: classify old branch and legacy functionality before any feature is allowed to return to Integration or MainLine.

## Classification

| Level | Meaning | Handling |
| --- | --- | --- |
| A | Current mainline has it and tests pass | Keep |
| B | Old branch has it, current target lacks it, value is clear | Scoped migration candidate |
| C | Old branch has it, but depends on old architecture | Extract ideas only |
| D | Fake implementation or obsolete behavior | Archive, do not migrate |
| E | Unknown | Create audit task before migration |

## Triage Ledger

| Legacy Item | Source Branch/Path | Level | Current Target Gap | Direct Migration Allowed? | Reason | Required Next Action |
| --- | --- | --- | --- | --- | --- | --- |
| `codex/integration-labtools-ui-c2-carryover` UI Shell preview | `9d4edf3` | B | MainLine lacks accepted UI Shell baseline | no | Contains useful shell baseline but also high-risk non-shell content | UI Shell scoped migration plan |
| Project Management old implementation | needs source search | E | `9d4edf3` preview is regressed/image-like | no | Best source not identified | Project Management restore audit |
| LabTools old pages | needs source search | E | Current style and runtime status mixed | no | Page-by-page status unknown | Fill LabTools reconciliation ledger |
| Bioinformatics old/carryover pages | needs source search | E | Buttons/routes need route proof | no | Must avoid treating old pages as final UI | Fill UI route inventory |
| Meta old/carryover pages | needs source search | E | Phase 4 L3 exists separately, shell baseline unresolved | no | Must not overwrite Phase 4 proof | Fill UI route inventory |

## Rules

- Legacy features never return through whole-branch merge.
- `old-page` must remain labeled as old until redesigned or explicitly accepted.
- Placeholder, dry-run, and image-only surfaces are not complete features.

## B-Class Recovery Candidates From Historical UI Check

Source: `docs/ui/UI线路既往检查.md`. These items are B-class because old `dev/integration` lacks them while `codex/integration-labtools-ui-c2-carryover` records recovered UI page lines with clear value. B-class means scoped recovery planning is justified; it is not migration approval.

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
