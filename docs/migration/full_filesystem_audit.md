# Full Filesystem Audit For BioMedPilot Consolidation

Audit date: 2026-04-28

Primary integration root at audit time:

- `/Users/changdali/Documents/New project 2`

Recommended final product root:

- `/Users/changdali/Documents/BioMedPilot`

No files were deleted during this audit.

## Scanned Roots

| Path | Exists | Size | Use judgment | Migration action |
|---|---:|---:|---|---|
| `/Users/changdali/Documents/New project 2` | yes | 21M | Current BioMedPilot unified integration project. Contains shell, shared layer, both workspaces, tests, docs, and legacy snapshots. | Keep as working source; copy to final root. |
| `/Users/changdali/Documents/model9` | yes | 2.7G | Main Meta Analysis project and latest legacy source. Includes uncommitted work and large virtual environments. | Copy source subset to archive; do not move/delete. |
| `/Users/changdali/Documents/New project` | yes | 1.4G | Main Bioinformatics project. Includes GEO, TCGA/GTEx, tests, docs, and virtual environment. | Copy source subset to archive; do not move/delete. |
| `/Users/changdali/Documents/model9-main-clean` | yes | 210M | Older clean Meta baseline. Many files overlap with `model9` and current legacy snapshot. | Archive as duplicate/old-version candidate metadata; full copy not required now. |
| `/Users/changdali/Documents/model9-module4-analysis-profiles` | yes | 1.3M | Meta phase snapshot for analysis profiles. | Duplicate/old-version candidate. |
| `/Users/changdali/Documents/model9-module4-rule-consumer` | yes | 1.0M | Meta phase snapshot for rule consumer. | Duplicate/old-version candidate. |
| `/Users/changdali/Documents/model9-module4-rule-service` | yes | 1.0M | Meta phase snapshot for rule service. | Duplicate/old-version candidate. |
| `/Users/changdali/Documents/model9-module5-profile-consumption` | yes | 1.1M | Meta phase snapshot for profile consumption. | Duplicate/old-version candidate. |
| `/Users/changdali/Documents/model9-module6-profile-reporting` | yes | 1.1M | Meta phase snapshot for profile reporting. | Duplicate/old-version candidate. |
| `/Users/changdali/Documents/model9-pico-search-foundation` | yes | 1.1M | Meta phase snapshot for PICO/search foundation. | Duplicate/old-version candidate. |
| `/Users/changdali/Documents/model9-ui-reporting-summary-data` | yes | 1.2M | Meta phase snapshot for reporting summary UI. | Duplicate/old-version candidate. |
| `/Users/changdali/Documents/生信分析` | yes | 0B | Empty folder. | Ignore unless user assigns meaning. |
| `/Users/changdali/Documents/生信分析软件开发` | yes | 0B | Empty folder. | Ignore unless user assigns meaning. |
| `/Users/changdali/Documents/硕士实验结果` | yes | 0B | Empty folder in this scan. | Ignore; likely personal/research data area. |
| `/Users/changdali/Documents/AO_PI_染色拍照记录表模板.xlsx` | yes | 0B | Spreadsheet template, not BioMedPilot code. | Do not migrate. |
| `/Users/changdali/Documents/EndNote` | yes | 220K | EndNote support/plugin data. | Do not migrate into software project. |
| `/Users/changdali/Documents/GitHub` | yes | 80K | Generic GitHub folder. | Do not migrate unless user identifies a specific repo. |
| `/Users/changdali/Documents/Paradox Interactive` | yes | 2.2M | Unrelated application/game data. | Do not migrate. |

## Key Directory Contents

| Directory | Key files / folders found | Classification |
|---|---|---|
| `New project 2/app/main.py` | Unified startup entry. | BioMedPilot current |
| `New project 2/app/shell/` | Dashboard, sidebar, navigation, status panel. | BioMedPilot current UI |
| `New project 2/app/shared/` | Project Center, Task Center, feature availability, testing mode, settings, storage, environment. | BioMedPilot current shared/common |
| `New project 2/app/bioinformatics/` | Workspace, adapter namespace, services/pipelines/reports placeholders, legacy snapshot. | Bioinformatics module |
| `New project 2/app/meta_analysis/` | Workspace, service/profile/screening/extraction/analysis/report namespaces, legacy snapshot. | Meta Analysis module |
| `New project 2/tests/` | Unified smoke, integration, UI, shared tests. | Current tests |
| `New project 2/docs/` | Architecture, module boundaries, migration docs, user testing docs. | Current docs |
| `New project 2/scripts/` | `run_app.py`, `run_tests.py`, `package_app.py`. | Current scripts |
| `New project 2/assets/` | Icons/images/styles placeholders. | Current assets |
| `New project 2/project_storage/` | Project/data/task/report/test feedback structure. | Runtime storage structure |
| `model9/app/`, `model9/app_meta/` | PySide6 desktop shell and Meta-specific UI pages. | Meta source |
| `model9/literature/`, `model9/extraction/`, `model9/analysis/`, `model9/reporting/` | Literature import, dedup/screening, extraction, analysis, reporting modules. | Meta source |
| `model9/assets/`, `model9/packaging/` | Icons and bundle scripts. | Meta UI/packaging assets |
| `New project/geo_tool/` | GEO GUI, launcher, MeSH/query tools. | Bioinformatics source |
| `New project/geo_pipeline/`, `New project/geo_processing/` | GEO download/process/readiness/detection. | Bioinformatics source |
| `New project/tcga_gtex/` | TCGA/GTEx facade, adapters, processing, lexicon. | Bioinformatics source |
| `New project/ui/` | Module 3 sandbox UI. | Bioinformatics UI |

## File Category Counts

Counts exclude `.git`, virtual environments, `__pycache__`, `.pytest_cache`, `dist`, and `build`.

| Directory | Python | Markdown | Test files | Docs files | Assets | Scripts | Packaging | Config |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `model9` | 197 | 27 | 76 | 25 | 96 | 12 | 2 | 4 |
| `New project` | 84 | 9 | 14 | 3 | 1 | 7 | 0 | 2 |
| `New project 2` | 340 | 45 | 104 | 36 | 100 | 22 | 3 | 8 |
| `model9-main-clean` | 149 | 24 | 74 | 22 | 36 | 13 | 0 | 4 |
| `model9-module4-analysis-profiles` | 71 | 3 | 23 | 1 | 0 | 3 | 0 | 1 |
| `model9-module4-rule-consumer` | 66 | 3 | 22 | 1 | 0 | 3 | 0 | 1 |
| `model9-module4-rule-service` | 63 | 3 | 20 | 1 | 0 | 2 | 0 | 1 |
| `model9-module5-profile-consumption` | 73 | 3 | 24 | 1 | 0 | 3 | 0 | 1 |
| `model9-module6-profile-reporting` | 73 | 3 | 24 | 1 | 0 | 3 | 0 | 1 |
| `model9-pico-search-foundation` | 69 | 4 | 21 | 2 | 0 | 2 | 0 | 1 |
| `model9-ui-reporting-summary-data` | 76 | 3 | 26 | 1 | 0 | 3 | 0 | 1 |

## Meta Analysis Project Files

| Source | Examples | Recommendation |
|---|---|---|
| `model9/literature/` | `service.py`, `dedup.py`, `screening_service.py`, parsers/stores. | Keep as canonical Meta legacy source snapshot. |
| `model9/extraction/` | extraction models, stores, rule services. | Keep as Meta legacy source. |
| `model9/analysis/`, `model9/analysis_profiles/` | profile adapters, readiness, stores. | Keep as Meta legacy source. |
| `model9/reporting/` | reporting models/services/profile readiness. | Keep as Meta legacy source. |
| `model9/app/`, `model9/app_meta/` | PySide6 shell and Meta pages. | Keep as reference UI; integrate through adapters later. |
| `model9/assets/`, `model9/packaging/` | icons and bundle scripts. | Copy into archive; selected icons can later move to `assets/icons/`. |

## Bioinformatics Project Files

| Source | Examples | Recommendation |
|---|---|---|
| `New project/geo_tool/` | GEO launcher, PySide6 GUI, MeSH query helpers. | Keep as canonical Bioinformatics legacy source snapshot. |
| `New project/geo_pipeline/` | GEO download/process pipeline surfaces. | Keep as Bioinformatics legacy source. |
| `New project/geo_processing/` | dataset detector, validators, asset helpers. | Keep as Bioinformatics legacy source. |
| `New project/tcga_gtex/` | facade, adapters, processing, lexicon. | Keep as Bioinformatics legacy source. |
| `New project/ui/` | Module 3 sandbox UI. | Keep as reference UI; integrate later. |
| `New project/tests/`, `New project/docs/`, `New project/scripts/` | smoke tests, audit docs, rule builders. | Preserve in legacy archive. |

## BioMedPilot Current Unified Files

| Area | Path | Keep in final project |
|---|---|---|
| Startup | `New project 2/app/main.py` | yes |
| Desktop shell | `New project 2/app/shell/` | yes |
| Shared/common | `New project 2/app/shared/` | yes |
| Bioinformatics module | `New project 2/app/bioinformatics/` | yes |
| Meta module | `New project 2/app/meta_analysis/` | yes |
| Tests | `New project 2/tests/` | yes |
| Docs | `New project 2/docs/` | yes |
| Scripts | `New project 2/scripts/` | yes |
| Assets | `New project 2/assets/` | yes |
| Runtime storage skeleton | `New project 2/project_storage/` | yes, structure only |

## UI / Icons / Design Assets

| Path | Type | Recommendation |
|---|---|---|
| `model9/assets/` | Meta icons, PNG/ICNS/SVG contact sheets. | Archive; selectively promote final app icon later. |
| `model9/app/resources/icons/` | app icon PNG/ICNS. | Archive; candidate for final `assets/icons/`. |
| `New project/geo_tool/app/geo_tool_icon.svg` | GEO tool icon. | Archive; candidate for module icon. |
| `New project 2/assets/` | Final project asset folders. | Keep. |

## Tests

| Path | Status | Recommendation |
|---|---|---|
| `New project 2/tests/` | Current unified test suite. | Keep and run in final root. |
| `model9/tests/` | Meta legacy tests. | Archive with legacy source; later run via isolated compatibility runner. |
| `New project/tests/` | Bioinformatics legacy tests. | Archive with legacy source; later run via isolated compatibility runner. |
| `model9-module*/tests/` | Stage snapshot tests. | Duplicate/old-version candidates; do not migrate into active suite. |

## Documentation

| Path | Status | Recommendation |
|---|---|---|
| `New project 2/docs/` | Current architecture, module boundaries, migration, user testing. | Keep in final project. |
| `model9/docs/` | Meta legacy design/readiness docs. | Archive in `archive/legacy_sources/model9/docs/`. |
| `New project/docs/` | Bioinformatics legacy audits/baselines. | Archive in `archive/legacy_sources/bioinformatics_project/docs/`. |
| `model9-module*/docs/` | Older stage docs, mostly duplicated by later baselines. | Store as old-doc/duplicate candidate, not active docs. |

## Packaging

| Path | Status | Recommendation |
|---|---|---|
| `New project 2/scripts/package_app.py` | Current placeholder. | Keep. |
| `model9/packaging/` | Legacy Meta app bundle script and launcher. | Archive; do not make active packaging yet. |
| `model9/dist/`, `model9/build/` | Generated packaging output. | Do not migrate; mark ignore/needs_review. |

## Duplicate Candidates

Hash scanning found many identical files across `model9`, current legacy snapshots, and `model9-module*` directories. Examples:

| Duplicate group | Locations | Recommendation |
|---|---|---|
| `literature/batch_service.py` | `model9`, `New project 2/app/meta_analysis/legacy`, `model9-main-clean`, all `model9-module*` snapshots. | Keep active copy in final legacy source; archive module snapshots as duplicate candidates. |
| `literature/parser.py` | Same broad Meta snapshot set. | Duplicate candidate. |
| `fulltext/service.py` | Same broad Meta snapshot set. | Duplicate candidate. |
| `bias/models.py` | Same broad Meta snapshot set. | Duplicate candidate. |
| `tests/test_task_status.py` | Same broad Meta snapshot set. | Duplicate candidate. |
| `tcga_gtex/*` | `New project` and `New project 2/app/bioinformatics/legacy`. | Keep current final legacy copy; archive original source. |
| `geo_tool/*` | `New project` and `New project 2/app/bioinformatics/legacy`. | Keep current final legacy copy; archive original source. |

## Likely Old Versions

| Path | Reason |
|---|---|
| `model9-main-clean` | Older baseline; current `model9` and `New project 2` contain newer shell work. |
| `model9-module4-*` | Phase snapshots with repeated Meta code. |
| `model9-module5-profile-consumption` | Phase snapshot. |
| `model9-module6-profile-reporting` | Phase snapshot. |
| `model9-pico-search-foundation` | Phase snapshot. |
| `model9-ui-reporting-summary-data` | Phase snapshot. |

## Possible Misplaced Or Non-Project Files

| Path | Reason | Recommendation |
|---|---|---|
| `/Users/changdali/Documents/AO_PI_染色拍照记录表模板.xlsx` | Spreadsheet template; not app source. | Do not migrate. |
| `/Users/changdali/Documents/EndNote` | External app/plugin data. | Do not migrate. |
| `/Users/changdali/Documents/Paradox Interactive` | Unrelated application data. | Do not migrate. |
| `/Users/changdali/Documents/GitHub` | Generic location, no identified BioMedPilot source. | Do not migrate now. |
| `model9/.venv`, `model9/.venv-meta`, `New project/.venv` | Large virtual environments. | Do not copy to final project. |
| `model9/dist`, `model9/build` | Generated packaging output. | Do not copy to active project; archive only if user requests. |

## Suggested Final Retention

Keep in the final active project:

- Current BioMedPilot shell and shared layer from `New project 2`.
- Current module boundary packages under `app/bioinformatics` and `app/meta_analysis`.
- Current tests, docs, scripts, assets, and storage skeleton.
- Legacy snapshots under `app/*/legacy` for runtime/reference compatibility.

Archive, but do not activate:

- `model9` source subset.
- `New project` source subset.
- Small `model9-module*` old snapshots as duplicate candidates or old docs.

Do not migrate:

- Virtual environments.
- Build/dist outputs.
- Large or personal raw data unless later promoted to examples/fixtures.
- Unrelated application folders.

