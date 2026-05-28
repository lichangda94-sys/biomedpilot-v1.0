# B90 MainLine Enrichment Contract Convergence and Scoped Carry-over

## Scope

This stage carries the B81-B88 enrichment contract layer from `dev/bioinformatics` into MainLine by scoped cherry-pick. It does not publish ReleaseBuild, does not replace desktop entry points, and does not expand clinical interpretation.

MainLine baseline before carry-over:

- Branch: `codex/mainline-survival-clinical-carryover`
- Baseline HEAD: `7bcdb7f53430938db85bec25a87e48678283d2c4`

Bioinformatics source baseline:

- Branch: `dev/bioinformatics`
- Source HEAD before B89: `f2ec99df5596c32c5ffa11d0b21051fa406c9f30`
- B89 audit HEAD: `1ca371c241b8cfd320df68f789124976da272dc0`

## Carried Commits

The following B81-B88 commits were applied to MainLine:

| Stage | MainLine commit | Source intent |
| --- | --- | --- |
| B81 | `7c0bc88` | Enrichment resource registry gate |
| B82 | `8300338` | External R enrichment backend capability gate |
| B83 | `7d2f28a` | Controlled R enrichment adapter |
| B84 | `1b4b316` | Enrichment execution confirmation gate |
| B85 | `5aeefd1` | Enrichment result review export |
| B86 | `178a07f` | Enrichment plot and section report gates |
| B87 | `5e87171` | Enrichment layer closure audit |
| B88 | `48dbf7b` | Analysis UI enrichment execution controls |

## Conflict Resolution

B88 had expected conflicts in:

- `app/bioinformatics/analysis_ui/action_rules.py`
- `app/bioinformatics/workflow_pages.py`
- `tests/bioinformatics/test_analysis_ui_state.py`

Resolution policy:

- Preserve MainLine existing DEG and survival/clinical UI gates.
- Add enrichment actions only:
  - `enrichment_parameter_confirmation`
  - `controlled_ora`
  - `controlled_gsea_preranked`
  - `enrichment_result_review`
  - `enrichment_plot_artifact`
  - `enrichment_section_report`
- Keep full formal GSEA disabled beyond controlled preranked GSEA.
- Do not import later Bioinformatics multi-factor DEG UI fragments into MainLine in this stage.

One MainLine-specific read-only fix was applied during conflict resolution:

- `app/bioinformatics/enrichment_result_review.py` now reads `load_result_index(..., persist_generated=False)` when used by Analysis Center state.

This prevents Analysis Center read-only state construction from creating `manifests/result_manager.json` or `results/summaries/result_index.json`.

## MainLine Contract Status

MainLine now has the B81-B88 enrichment contract files:

- `app/bioinformatics/enrichment_resources.py`
- `app/bioinformatics/enrichment_backend.py`
- `app/bioinformatics/enrichment_r_adapter.py`
- `app/bioinformatics/enrichment_execution_gate.py`
- `app/bioinformatics/enrichment_result_review.py`
- `app/bioinformatics/enrichment_plot_report.py`
- `app/bioinformatics/enrichment_e2e_audit.py`

Analysis UI now exposes enrichment gate state and disabled reasons without implying full formal GSEA completion. Controlled ORA/GSEA remain gated by formal source result, resource, backend detection, parameter confirmation, result schema, plot/report section eligibility, and report boundary rules.

## Boundary Checks

Maintained boundaries:

- No GSEA mode beyond controlled preranked GSEA was enabled.
- No survival or clinical interpretation was added.
- No report-ready bypass was added.
- No external R/Bioconductor package installation or bundling was added.
- Detector availability is not treated as execution readiness.
- Imported/testing/exploratory/preflight results are not promoted to formal enrichment results.

## Validation

Commands run on MainLine after scoped convergence:

| Command | Result |
| --- | --- |
| `git diff --check` | passed |
| `python3 -m pytest tests/bioinformatics -q -k "enrichment or gsea or gene_set or analysis_ui"` | 66 passed |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or enrichment or gsea"` | 8 passed |
| `python3 -m pytest tests/bioinformatics -q` | 509 passed, 1 warning |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` | 198 passed |
| `python3 -m app.main --smoke-test` | passed, `git_head=48dbf7b` |
| `python3 scripts/package_app.py --smoke-test` | passed, `git_head=48dbf7b` |
| `open -W -n dist/BioMedPilot.app --args --smoke-test` | passed |
| `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app` | passed |

## ReleaseBuild Receive Guidance

ReleaseBuild should receive this MainLine convergence only after its unrelated dirty files are resolved or explicitly preserved.

Do not merge `dev/bioinformatics` wholesale into ReleaseBuild. ReleaseBuild contains existing structured packages:

- `app/bioinformatics/enrichment/`
- `app/bioinformatics/gsea/`

Those files must be preserved until a separate convergence stage maps them to the B81-B88 contract surface.

Recommended next stage:

- B91 ReleaseBuild Enrichment Receive-from-MainLine and Closure Gate.

Expected B91 approach:

1. Start from the current ReleaseBuild candidate.
2. Preserve unrelated DEG/input-adaptation work.
3. Receive MainLine enrichment convergence from `48dbf7b` or a later B90 closure commit.
4. Resolve duplicate enrichment/GSEA surfaces by contract mapping, not source-tree overwrite.
5. Run ReleaseBuild bioinformatics/UI/package/open-W/codesign gates.

## Blocker / Major / Minor

### Blocker

- None in MainLine after scoped convergence.

### Major

- ReleaseBuild still requires a receive-from-MainLine stage because it has older structured ORA/GSEA modules and unrelated dirty files.

### Minor

- MainLine enrichment runtime remains detect-first and depends on the user's external R environment at runtime.

## Final Conclusion

MainLine enrichment contract convergence is complete as a scoped carry-over. Proceed to ReleaseBuild receive and closure before starting the next analysis-method development track.
