# Deprecated Legacy Register

Date: 2026-06-04

## Purpose

This register identifies legacy paths that must not be migrated directly or counted as current completion evidence. They may be useful for requirements archaeology, fixtures, resource review, or UI inspiration, but they are not current runtime sources.

Current audit baseline:

```text
branch: dev/bioinformatics
HEAD: b77805c242d4f1a47a4cca20fcf21fb3ac4c6e15
audit mode: read-only Phase 2.5 refresh
```

## Deprecated / Quarantined Items

| Item | Source | Why deprecated | Current replacement / allowed use | Migration status |
| --- | --- | --- | --- | --- |
| Standalone Bio GEO GUI | `app/bioinformatics/legacy/geo_tool/main.py`, `run_geo_tool.py`, archive copy | Separate historical app with old contracts and launchers | Current Bio UI pages plus search/recognition/standardization services | Do not import; reference only |
| Bio legacy GEO workflow | `legacy/geo_tool/geo_workflow.py`, `geo_pipeline/**`, `geo_processing/**` | Old GEO mainline, duplicate surfaces, compatibility wrappers | Current resolver and standardized asset contracts | Deprecated/direct-use forbidden |
| Bio literature utilities | `app/bioinformatics/legacy/literature_cli.py`, `literature_gui.py` | Bio no longer owns PubMed/PICO/literature workflows | Current Meta literature workflow | Deprecated for Bio |
| Legacy download scripts | `download_geo_full_only.py`, `process_geo_family_soft.py`, `download_supplement_and_sra.py` | Compatibility scripts outside current UI/task contracts | Current downloader/search/recognition services | Deprecated |
| Legacy TCGA/GTEx facade | `app/bioinformatics/legacy/tcga_gtex/**` | Old optional runtime/facade and mockable locator contracts | Current `data_sources`, `tcga`, `standard_assets` after audit | Rewrite only |
| Archive duplicate Bio source | `archive/legacy_sources/bioinformatics_project/**` | Archived duplicate of old Bio source | File archaeology only | Deprecated as runtime |
| Meta old workbench shell | `app/meta_analysis/legacy/app/**`, `app_meta/**`, archive `model9/app/**` | Separate UI shell; current UI is the only mainline | Current `app/meta_analysis/pages/**` | Deprecated as runtime |
| Meta fake GEO readiness | `app/meta_analysis/legacy/geo_readiness/**`, `legacy/analysis/deg_ready_matrix.py` | Belongs to old snapshot and Bio boundary; metadata/fake preflight risk | Current Bio recognition/resolver/DEG gates | Deprecated for Meta |
| Meta task mock/no-op runner | `app/meta_analysis/legacy/core/task_runner_adapters.py`, task runner docs | Historical dry-run/no-op contract; not real analysis output | Current task/result contracts only if reimplemented | Do not count as real run |
| Meta legacy reporting placeholders | `app/meta_analysis/legacy/reporting/**`, old reporting docs, archive copy | Historical report summaries, not tied to current canonical result contract | Current `formal_report_service`, `publication_export_service`, Meta result contract bridge | Adapter/rewrite only |
| Legacy package scripts | `app/meta_analysis/legacy/packaging/**`, `legacy/scripts/check_packaging_readiness.py` | Standalone package flow, not current app bundle source | Current root `scripts/package_app.py` | Deprecated |
| Legacy icons/contact sheets | `app/meta_analysis/legacy/assets/**` | Visual assets only, not functionality | May be reviewed by UI design | Ignore for analysis capability |
| Legacy bytecode/cache artifacts | `app/bioinformatics/legacy/**/__pycache__/**`, `app/meta_analysis/legacy/**/__pycache__/**` if present | Interpreter cache files from old runs; not source or reproducible evidence | Ignore; do not migrate or cite as implementation | Deprecated |
| Archive duplicate model9 source | `archive/legacy_sources/model9/**` | Archived duplicate of old Meta workbench and task/report stack | File archaeology only | Deprecated as runtime |
| Old pre-B8 DEG preflight | `codex/stage-3.6-deg-preflight`, old `deg_executor_preflight.py` variants | Predates current B8/B9+ result/input contracts | Current DEG formal gates | Superseded |
| Old GEO search UI branches | `codex/bio-search-ui-main*`, `codex/bio-ui-download-integration`, `codex/bio-geo-real-download-test` | Older UI copy/search logic and partial recognition | Current Bio search/recognition pages | Reference only |
| Old Meta workflow UI branch | `codex/meta-workflow-ui`, `codex/meta-analysis-refresh` | Early UI integration, superseded by current pages | Current Meta pages/workflow dashboard | Reference only |
| Old UI shell branches | `dev/ui-shell`, `integration/release-ui-shell-scoped-migration` | UI shell/design branch state is not the current Bio/Meta runtime | Current UI only; UI owner may select scoped assets later | Design reference only |
| Branch-only risk/nomogram clinical claims | `codex/releasebuild-formal-deg-carryover`, `dev/release-internal-test` risk artifacts | High risk of overclaiming clinical prediction/prognosis | Only gated, non-clinical research outputs if reimplemented | Do not migrate as clinical feature |

## Not Deprecated, But Not A Production Claim

The following are current or current-adjacent, but still require focused proof before release or production claims:

- Current Bio controlled formal DEG.
- Current Bio controlled ORA/GSEA.
- Current Bio controlled KM/log-rank and Cox.
- Current Bio risk score candidate gates.
- Current Meta v2 statistics engine.
- Current Meta result contract bridge.
- Current analysis runtime mock bridge.
- Current standard analysis mock/lite worker scaffold.

None of these should be described as clinical-grade, public-release ready, or full production analysis unless a later phase proves that standard with current UI, current contracts, real outputs, and tests.

Current mock/lite worker scaffold is not deprecated, but it is quarantined as testing-level infrastructure until a selected module proves current UI entry, real input, real engine, standard package output, result discovery, and tests in one focused phase.
