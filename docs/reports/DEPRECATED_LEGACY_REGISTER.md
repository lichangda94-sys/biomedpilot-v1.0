# Deprecated Legacy Register

Date: 2026-06-05

Baseline: `dev/bioinformatics` at `00503b1df6d05645be4efd447626f81e6999e254`

## Rule

Deprecated means the item must not be migrated by direct import, direct UI call, wholesale path checkout, or branch merge. Some items may still be used as requirements or reference material after a scoped design review.

This register was refreshed against current `dev/bioinformatics` HEAD `00503b1d`. No deprecated item below was executed, imported, or promoted.

## Deprecated / Quarantined Items

| Item | Source | Why deprecated or quarantined | Current UI mapping | Runtime evidence | Tests | Risk | Allowed future use |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Old standalone GEO Tool app | `app/bioinformatics/legacy/geo_tool/**`, `archive/legacy_sources/bioinformatics_project/geo_tool/**` | Standalone workflow, old entrypoints, old dependencies, bypasses current resolver/result contracts | Conceptual only: Bio Data Source/Search | Not run in this audit | Legacy-only | High | Requirements/reference only; rewrite adapters if needed |
| Legacy GEO pipeline scripts | `legacy/geo_pipeline/**`, `download_geo_full_only.py`, `download_supplement_and_sra.py`, `process_geo_family_soft.py` | Network/file operations and outputs predate current source registry and standardization contracts | Conceptual only: acquisition/download | Not run | Legacy-only | High | Extract documented rules only |
| Legacy fake/preflight task paths | `app/meta_analysis/legacy/scripts/run_fake_geo_preflight.py`, legacy task runner mock/dry-run tests | Explicit fake/dry-run behavior cannot be counted as real analysis | None | No current real output | Legacy-only | High | Do not migrate |
| Legacy Bio literature CLI/GUI | `app/bioinformatics/legacy/literature_cli.py`, `literature_gui.py` | Literature belongs to Meta line; old UI would blur Bio/Meta boundaries | Meta literature pages are separate current implementation | Not run | Legacy-only | High | Deprecated for Bio; reference only for Meta import requirements |
| Legacy TCGA/GTEx facade direct runner | `app/bioinformatics/legacy/tcga_gtex/facade.py`, `download/task_runner.py` | Old locator/task-run contract and direct execution risk | Current TCGA/GTEx source cards use newer services | Not run | Legacy-only | High | Rewrite through current source/standardization/resolver contracts |
| Legacy Bio sandbox UI | `app/bioinformatics/legacy/ui/module3_sandbox.py` | Old sandbox widget with no current mainline page | None | Not run | Legacy-only | High | UI reference only |
| Old Meta workbench shell | `app/meta_analysis/legacy/app/**`, `legacy/app_meta/**` | Separate app shell/sidebar/router; would replace current UI | None; current Meta pages are under `app/meta_analysis/pages/**` | Not run | Legacy-only | High | Deprecated; visual reference only |
| Legacy Meta task runner/store | `app/meta_analysis/legacy/core/task_*.py`, `legacy/scripts/run_task_once.py` | Old task state and dry-run behavior conflict with current canonical result contracts | None | Not run | Legacy-only | High | Rewrite concepts only |
| Legacy Meta analysis profile stack | `app/meta_analysis/legacy/analysis/**`, `analysis_profiles/**` | Old profile/readiness store not tied to v2 `run_id`/hash contract | Current Meta Analysis page uses v2 services | Not run | Legacy-only | High | Requirements reference only |
| Legacy Meta reporting service/widgets | `legacy/reporting/**`, `legacy/app/reporting_summary_widget.py` | Old reporting summaries are not bound to current canonical run/artifact contract | Current Reporting page has separate current services | Not run | Legacy-only | Medium/high | Adapter only after contract mapping |
| Legacy bias/readiness/profile helpers | `legacy/bias/**`, `legacy/core/profile_*` | Useful concepts but old project/profile state | Meta Quality/Reporting pages only conceptually | Not run | Legacy-only | Medium/high | Rewrite/adapt after selected scope |
| Archive mirrors | `archive/legacy_sources/**` | Mirrors old source trees and can double-count stale behavior | None | Not run | Archive-only | High | Provenance/reference only |
| Branch-only UI screenshots/static icons | `dev/ui-shell`, legacy assets/contact sheets | Design assets are not analysis functionality | UI design only | Not analysis runtime | Branch/asset evidence only | Medium | Design reference with UI owner review |
| Branch-only risk/nomogram clinical interpretation material | `dev/release-internal-test` risk/advanced visualization history | Clinical overclaim risk; not proven current production loop | No proven current production UI completion | Not run in this audit | Branch/current inventory only | High | Rewrite under strict clinical boundary |
| Branch-only OCR/fulltext workers | `dev/meta-analysis` | External OCR runtime and branch package divergence; not proven current L3 | Current fulltext pages only partially map | Not run in this audit | Branch/current inventory only | High | Adapter/rewrite after focused proof |

## Explicit Non-Completion Rules

| Pattern | Status |
| --- | --- |
| Mock/lite standard worker fixtures | Scaffolds only; not production analysis proof. |
| Branch-only plot/report files | Candidate material only until a current result source, semantics, and artifact registration are proven. |
| Legacy tests | Historical evidence only; not current UI/runtime proof. |
| Placeholder/demo files | Not completed functionality. |
| Preflight-only outputs | Input checks only; not formal analysis results. |
| Testing-level Meta reports | Testing artifacts only; not production or clinical reports. |
| Clinical interpretation/prognosis/treatment advice | Not allowed as a completed feature in current Bio/Meta lines. |

## Register Conclusion

Deprecated legacy items should remain quarantined. Future work may reference them only through a narrowly scoped migration task that starts from a current UI entry and proves current contracts, tests, and real output.
