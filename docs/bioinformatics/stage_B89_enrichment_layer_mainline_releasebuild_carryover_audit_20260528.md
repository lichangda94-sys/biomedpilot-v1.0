# B89 Enrichment Layer MainLine / ReleaseBuild Carry-over Audit

## Scope

This audit checks whether the B81-B88 enrichment layer can be carried from `dev/bioinformatics` into MainLine and ReleaseBuild. It is an audit and carry-over plan only. It does not merge branches, publish ReleaseBuild, replace desktop entry points, or expand clinical/report interpretation.

Baseline inspected:

- Bioinformatics HEAD: `f2ec99df5596c32c5ffa11d0b21051fa406c9f30`
- MainLine HEAD: `7bcdb7f53430938db85bec25a87e48678283d2c4`
- ReleaseBuild HEAD: `e02d58eab276b31a7b72d954e0ec282d5f31469e`

## Current State

### Bioinformatics

B81-B88 are present and validated:

- `enrichment_resources.py`
- `enrichment_backend.py`
- `enrichment_r_adapter.py`
- `enrichment_execution_gate.py`
- `enrichment_result_review.py`
- `enrichment_plot_report.py`
- `enrichment_e2e_audit.py`
- Analysis UI state/action wiring
- workflow page gate/action table exposure
- focused tests for resource, backend, adapter, confirmation, review, plot/report, closure, and UI

Untracked items intentionally excluded:

- `docs/bioinformatics/Bioinformatics_handoff_report_20260513.md`
- `project_storage/bioinformatics/`

### MainLine

MainLine is clean, but does not contain the B81-B88 enrichment contract files. It has Analysis UI surfaces, but not the new enrichment resource/backend/execution/review/plot/report/audit modules.

### ReleaseBuild

ReleaseBuild is not clean:

- modified `app/bioinformatics/analysis_ui/state.py`
- modified `app/bioinformatics/deg_engine/__init__.py`
- modified `tests/bioinformatics/test_analysis_ui_state.py`
- untracked `app/bioinformatics/deg_engine/input_adaptation.py`
- untracked `tests/bioinformatics/test_deg_input_adaptation_gate.py`
- untracked `docs/release/ReleaseBuild_handoff_report_20260513.md`
- untracked `project_storage/external_engines/`

ReleaseBuild has an older structured enrichment/GSEA implementation under:

- `app/bioinformatics/enrichment/`
- `app/bioinformatics/gsea/`

These files must not be deleted by a broad merge. They need a scoped convergence review against B81-B88 contracts.

## External R Enrichment Runtime

ReleaseBuild external detector payload now reports:

- status: `passed`
- Rscript: `/usr/local/bin/Rscript`
- R version: `R version 4.4.2 (2024-10-31)`
- architecture: `arm64`
- capabilities:
  - `ora_enricher=True`
  - `ora_go=True`
  - `ora_kegg=True`
  - `ora_reactome=True`
  - `gsea_preranked_fgsea=True`
  - `gsea_preranked_clusterprofiler=True`
  - `enrichment_plot_dotplot=True`
  - `enrichment_plot_barplot=True`
  - `gsea_plot_curve=True`
- warnings:
  - `optional_r_package_missing:pathview:package_not_installed_or_not_on_libpaths:pathview`

This clears the prior ReactomePA/msigdbr blocker at detector level, but B81-B88 still require explicit resource, parameter, confirmation, output schema, plot, and section report gates before those capabilities are exposed.

## File Coverage

| File / area | Bioinformatics | MainLine | ReleaseBuild | Carry-over note |
| --- | --- | --- | --- | --- |
| `app/bioinformatics/enrichment_backend.py` | present | missing | missing | carry over |
| `app/bioinformatics/enrichment_r_adapter.py` | present | missing | missing | carry over; Rscript adapter remains detect-first |
| `app/bioinformatics/enrichment_execution_gate.py` | present | missing | missing | carry over |
| `app/bioinformatics/enrichment_result_review.py` | present | missing | missing | carry over |
| `app/bioinformatics/enrichment_plot_report.py` | present | missing | missing | carry over |
| `app/bioinformatics/enrichment_e2e_audit.py` | present | missing | missing | carry over |
| `app/bioinformatics/enrichment_resources.py` | present | missing | missing | carry over |
| `app/bioinformatics/gene_set_resources.py` | present | present | present | scoped hunk review required |
| `app/bioinformatics/analysis_ui/state.py` | present | present | present | scoped hunk review required; ReleaseBuild dirty |
| `app/bioinformatics/analysis_ui/action_rules.py` | present | present | present | scoped hunk review required |
| `app/bioinformatics/workflow_pages.py` | present | present | present | scoped hunk review required |
| `tests/bioinformatics/test_enrichment_*` B81-B88 | present | missing | missing | carry over |
| `tests/ui/test_bioinformatics_workflow_pages.py` | present | present | present | scoped hunk review required |

## Difference Risk

Direct merge from `dev/bioinformatics` into ReleaseBuild is not recommended.

Reasons:

- ReleaseBuild contains older `app/bioinformatics/enrichment/` and `app/bioinformatics/gsea/` packages that are absent from `dev/bioinformatics`; a broad merge can appear as deletes.
- ReleaseBuild has a dirty worktree with unrelated DEG/input-adaptation changes.
- MainLine lacks B81-B88, so ReleaseBuild should not receive enrichment directly from Bioinformatics without first converging MainLine.
- The external R detector now passes, so the receiving branch must preserve detect-first runtime policy and not accidentally treat detector availability as automatic formal execution readiness.

## Recommended Carry-over Strategy

Recommendation: **scoped carry-over, MainLine first, then ReleaseBuild receive-from-MainLine**.

1. Clean or stash unrelated ReleaseBuild work before receiving anything.
2. Carry B81-B88 into MainLine by scoped cherry-pick or file-level application, not broad merge.
3. Preserve existing MainLine recognition / standardization / resolver / DEG / survival contracts.
4. In MainLine, run focused enrichment tests plus full Bioinformatics/UI tests.
5. Only after MainLine passes, let ReleaseBuild receive the converged MainLine result.
6. In ReleaseBuild, do not delete existing `app/bioinformatics/enrichment/` or `app/bioinformatics/gsea/` packages until a separate convergence stage maps them to B81-B88 contracts.
7. Keep external R runtime detect-first; do not bundle or auto-install R/Bioconductor packages.

## Blocker / Major / Minor

### Blocker

- ReleaseBuild worktree is dirty and should not receive carry-over until unrelated local changes are resolved or explicitly preserved.
- MainLine does not yet contain B81-B88, so ReleaseBuild direct receive is not recommended.

### Major

- ReleaseBuild has older structured enrichment/GSEA modules. Broad merge risks deleting or bypassing them. A convergence plan is required.
- Detector status now passes for ReactomePA/msigdbr-related capability, but UI and execution must still require resource/parameter/confirmation/result schema gates before exposing those paths.

### Minor

- Optional `pathview` remains missing. This should remain a warning unless a future pathway diagram feature explicitly requires it.
- Existing old handoff/project_storage artifacts remain excluded from commits.

## Rollback Plan

If carry-over causes failures:

1. Revert the scoped carry-over commit on the receiving branch.
2. Preserve ReleaseBuild old `app/bioinformatics/enrichment/` and `app/bioinformatics/gsea/` packages.
3. Re-run previous ReleaseBuild gate tests.
4. Re-attempt as smaller groups:
   - B81/B82 resource and backend gates;
   - B83/B84 adapter and confirmation gates;
   - B85/B86 review, plot, report section;
   - B87/B88 audit and UI wiring.

## Suggested Next Commands

MainLine scoped receive:

```bash
cd "/Users/changdali/Developer/biomedpilot v1.0/MainLine"
git status
git cherry-pick 2fb75f7 28d4ad1 c1bc957 8aed8f5 79560b5 0039442 f2ec99d
git diff --check
python3 -m pytest tests/bioinformatics -q -k "enrichment or gsea or gene_set or analysis_ui"
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or results_browser or settings or gsea or enrichment"
python3 -m app.main --smoke-test
```

ReleaseBuild receive after MainLine passes:

```bash
cd "/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild"
git status
# preserve or commit unrelated dirty DEG/input-adaptation work first
# receive the MainLine convergence commit rather than merging Bioinformatics wholesale
git diff --check
python3 -m pytest tests/bioinformatics -q -k "enrichment or gsea or gene_set or analysis_ui"
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q -k "bioinformatics"
python3 -m app.main --smoke-test
python3 scripts/package_app.py --smoke-test
open -W -n dist/BioMedPilot.app --args --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```

## Final Recommendation

Proceed to **B90 MainLine Enrichment Contract Convergence and Scoped Carry-over**.

Do not start ReleaseBuild carry-over execution until MainLine has absorbed B81-B88 and ReleaseBuild dirty files are resolved or explicitly preserved.
