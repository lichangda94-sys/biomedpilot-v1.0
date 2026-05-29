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
