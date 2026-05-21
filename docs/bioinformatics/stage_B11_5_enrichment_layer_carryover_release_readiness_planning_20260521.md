# Bioinformatics B11.5 Enrichment Layer Carry-over / Release-Readiness Planning

Date: 2026-05-21

Current branch: `codex/releasebuild-formal-deg-carryover`

Current HEAD: `889f30657d593d8a997b1cda44b79beb777d1560` (`harden Bioinformatics enrichment layer closure`)

Planning conclusion: **ready for scoped carry-over planning; release packaging gates must be rerun before any release candidate is declared ready.**

## 1. Current Enrichment Layer File Inventory

Core ORA layer:

```text
app/bioinformatics/enrichment/__init__.py
app/bioinformatics/enrichment/closure_audit.py
app/bioinformatics/enrichment/dependency_check.py
app/bioinformatics/enrichment/e2e_audit.py
app/bioinformatics/enrichment/executor.py
app/bioinformatics/enrichment/export.py
app/bioinformatics/enrichment/gene_set_gate.py
app/bioinformatics/enrichment/input_gate.py
app/bioinformatics/enrichment/models.py
app/bioinformatics/enrichment/parameter_gate.py
app/bioinformatics/enrichment/result_schema.py
app/bioinformatics/enrichment/review.py
```

Core GSEA layer:

```text
app/bioinformatics/gsea/__init__.py
app/bioinformatics/gsea/dependency_check.py
app/bioinformatics/gsea/e2e_audit.py
app/bioinformatics/gsea/executor.py
app/bioinformatics/gsea/export.py
app/bioinformatics/gsea/gene_set_gate.py
app/bioinformatics/gsea/input_gate.py
app/bioinformatics/gsea/models.py
app/bioinformatics/gsea/parameter_gate.py
app/bioinformatics/gsea/rank_metric_gate.py
app/bioinformatics/gsea/result_schema.py
app/bioinformatics/gsea/review.py
```

Plot/report/UI surfaces touched by enrichment closure:

```text
app/bioinformatics/plots/ora.py
app/bioinformatics/plots/gsea.py
app/bioinformatics/plots/schema.py
app/bioinformatics/plots/models.py
app/bioinformatics/reports/ora.py
app/bioinformatics/reports/gsea.py
app/bioinformatics/reports/formal_deg.py
app/bioinformatics/reports/e2e_audit.py
app/bioinformatics/reports/project_report_builder.py
app/bioinformatics/analysis_ui/action_rules.py
app/bioinformatics/analysis_ui/state.py
app/bioinformatics/workflow_pages.py
```

Release-gate test inventory:

```text
tests/bioinformatics/test_ora_input_gate.py
tests/bioinformatics/test_ora_gene_set_gate.py
tests/bioinformatics/test_ora_parameter_gate.py
tests/bioinformatics/test_ora_result_schema_gate.py
tests/bioinformatics/test_ora_execution.py
tests/bioinformatics/test_ora_result_review.py
tests/bioinformatics/test_ora_plot_artifact.py
tests/bioinformatics/test_ora_report_ready.py
tests/bioinformatics/test_ora_e2e_acceptance_audit.py
tests/bioinformatics/test_gsea_input_gate.py
tests/bioinformatics/test_gsea_rank_metric_gate.py
tests/bioinformatics/test_gsea_gene_set_gate.py
tests/bioinformatics/test_gsea_parameter_gate.py
tests/bioinformatics/test_gsea_result_schema_gate.py
tests/bioinformatics/test_gsea_execution.py
tests/bioinformatics/test_gsea_result_review.py
tests/bioinformatics/test_gsea_plot_artifact.py
tests/bioinformatics/test_gsea_report_ready.py
tests/bioinformatics/test_gsea_e2e_acceptance_audit.py
tests/bioinformatics/test_enrichment_layer_closure_audit.py
tests/ui/test_bioinformatics_workflow_pages.py
```

## 2. DEG / ORA / GSEA Result Semantics Stability

Status: **stable for release-gate planning.**

Current semantics boundary:

| Result type | task_type | Allowed semantics | Release boundary |
|---|---|---|---|
| Formal DEG | `deg` | `formal_computed_result` | two-group controlled DEG MVP only |
| Imported DEG | `deg` or imported result rows | `imported_external_result` | review/imported provenance only |
| Formal DEG-derived ORA | `ora_enrichment` | `formal_computed_result` | source must be formal DEG result index entry |
| Imported DEG-derived ORA | `ora_enrichment` | `imported_external_result` | must carry imported-derived warning; not formal recomputed ORA |
| Formal DEG-derived GSEA | `gsea_preranked` | `formal_computed_result` | source must be formal DEG result index entry |
| Imported DEG-derived GSEA | `gsea_preranked` | `imported_external_result` | must carry imported-derived warning; not formal recomputed GSEA |
| Preflight/testing/exploratory | any | `preflight_only`, `testing_level`, `exploratory` | blocked from formal plot/report-ready |

B11.4 `audit_enrichment_layer_closure()` passed on repo-root audit and fixture coverage. It checks source lineage, dependency snapshots, gene set registry, plot artifact ownership, section-only report package manifests, and UI disabled states.

## 3. ORA/GSEA Tests as Release Gates

Status: **yes, ORA/GSEA tests are suitable as release gates.**

Minimum release gate subset:

```text
python3 -m pytest tests/bioinformatics/test_ora_input_gate.py \
  tests/bioinformatics/test_ora_gene_set_gate.py \
  tests/bioinformatics/test_ora_parameter_gate.py \
  tests/bioinformatics/test_ora_result_schema_gate.py \
  tests/bioinformatics/test_ora_execution.py \
  tests/bioinformatics/test_ora_result_review.py \
  tests/bioinformatics/test_ora_plot_artifact.py \
  tests/bioinformatics/test_ora_report_ready.py \
  tests/bioinformatics/test_ora_e2e_acceptance_audit.py \
  tests/bioinformatics/test_gsea_input_gate.py \
  tests/bioinformatics/test_gsea_rank_metric_gate.py \
  tests/bioinformatics/test_gsea_gene_set_gate.py \
  tests/bioinformatics/test_gsea_parameter_gate.py \
  tests/bioinformatics/test_gsea_result_schema_gate.py \
  tests/bioinformatics/test_gsea_execution.py \
  tests/bioinformatics/test_gsea_result_review.py \
  tests/bioinformatics/test_gsea_plot_artifact.py \
  tests/bioinformatics/test_gsea_report_ready.py \
  tests/bioinformatics/test_gsea_e2e_acceptance_audit.py \
  tests/bioinformatics/test_enrichment_layer_closure_audit.py -q
```

Recommended broader release gate:

```text
python3 -m pytest tests/bioinformatics -q -k "formal_deg or ora or gsea or enrichment or result_semantics or plot or report or e2e or analysis_ui"
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or results_browser or report"
python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
python3 -m app.main --smoke-test
```

Most recent B11.4 verification before this planning doc:

```text
git diff --check: passed
tests/bioinformatics/test_enrichment_layer_closure_audit.py: 4 passed
bioinformatics keyword gate: 182 passed, 343 deselected
UI keyword gate: 15 passed, 96 deselected
full tests/bioinformatics: 525 passed
full tests/ui: 268 passed
source smoke: passed
```

## 4. Analysis UI Separation

Status: **stable.**

Analysis UI separates:

- Formal DEG: enabled only through formal DEG gates and user confirmation.
- Imported DEG review: review-only with `imported_external_result` semantics.
- ORA readiness/run/plot/report actions: ORA-specific gates and ORA-specific disabled reasons.
- GSEA readiness/run/plot/report actions: GSEA-specific gates and GSEA-specific disabled reasons.
- Survival / KM / Cox / log-rank / HR: disabled or preflight-only rows.
- Clinical association: preflight/design-only; no formal statistics or clinical advice.

The UI wording explicitly avoids presenting preflight, imported, exploratory, or testing outputs as formal computed results.

## 5. Report Package Boundary

Status: **section-only; not full integrated report.**

Current package scopes:

| Package | section_scope | Full integrated report? |
|---|---|---|
| Formal DEG | `formal_deg_only` | No |
| Formal ORA | `formal_ora_only` | No |
| Imported-derived ORA | `imported_derived_ora_only` | No |
| Formal GSEA | `formal_gsea_only` | No |
| Imported-derived GSEA | `imported_derived_gsea_only` | No |

Report package manifests preserve:

- `survival_enabled=false`
- `clinical_conclusion_enabled=false`
- limitations / warnings / provenance
- package-internal stable directories
- table-only mode text where applicable

Full integrated reports remain out of scope.

## 6. ReleaseBuild Formal DEG Candidate vs B10/B11 Fork Status

Current branch history shows the ReleaseBuild candidate is linear from formal DEG carry-over into ORA/GSEA:

```text
1430b70 feat(bio): carry over formal DEG MVP to ReleaseBuild
6600fd6 add Bioinformatics ORA input and resource gates
46e8e57 add Bioinformatics controlled ORA execution
6a24258 add Bioinformatics ORA plot artifact gate
788aa28 add Bioinformatics ORA report-ready gate
e2b9df9 add Bioinformatics GSEA preranked gates
1fb5c2b add Bioinformatics controlled preranked GSEA execution
c6d0dea add Bioinformatics GSEA plot and report gates
889f306 harden Bioinformatics enrichment layer closure
```

Conclusion: **within this ReleaseBuild branch, formal DEG and B10/B11 are not functionally forked.** B10/B11 are layered on the formal DEG candidate and use result index source semantics rather than duplicating formal DEG execution.

However, branch comparison shows:

- `stable/mainline` baseline `be8c924` does not contain B10/B11 enrichment layer.
- `dev/bioinformatics` is behind this ReleaseBuild B10/B11 closure and lacks current ORA/GSEA closure files.
- `dev/release-internal-test` is behind this candidate and lacks the formal DEG + B10/B11 scoped carry-over chain.

## 7. Need Scoped Carry-over to MainLine?

Recommendation: **yes, if MainLine is expected to contain the closed enrichment MVP.**

Use scoped carry-over from current ReleaseBuild branch to the chosen MainLine branch. Do not broad-merge unrelated release docs or historical doc deletions. Suggested scope:

```text
app/bioinformatics/enrichment/
app/bioinformatics/gsea/
app/bioinformatics/plots/ora.py
app/bioinformatics/plots/gsea.py
app/bioinformatics/plots/models.py
app/bioinformatics/plots/schema.py
app/bioinformatics/plots/__init__.py
app/bioinformatics/reports/ora.py
app/bioinformatics/reports/gsea.py
app/bioinformatics/reports/formal_deg.py
app/bioinformatics/reports/e2e_audit.py
app/bioinformatics/reports/project_report_builder.py
app/bioinformatics/reports/__init__.py
app/bioinformatics/analysis_ui/
app/bioinformatics/workflow_pages.py
tests/bioinformatics/test_ora_*.py
tests/bioinformatics/test_gsea_*.py
tests/bioinformatics/test_enrichment_layer_closure_audit.py
tests/bioinformatics/test_plot_artifact_schema.py
tests/bioinformatics/test_plot_semantics_inheritance.py
tests/ui/test_bioinformatics_workflow_pages.py
docs/bioinformatics/stage_B10_*.md
docs/bioinformatics/stage_B11_*.md
```

Before MainLine carry-over, re-run the MainLine recognition/standardization and formal DEG gates to ensure B10/B11 source result discovery still resolves correctly.

## 8. Need Scoped Carry-over to ReleaseBuild Candidate?

Recommendation: **depends which branch is named the release candidate.**

- If `codex/releasebuild-formal-deg-carryover` becomes the ReleaseBuild candidate, no additional scoped carry-over is needed for B10/B11; this branch already contains the closed enrichment layer.
- If `dev/release-internal-test` remains the ReleaseBuild candidate, scoped carry-over is needed from current HEAD because `dev/release-internal-test` is behind formal DEG and B10/B11.

Do not use a broad merge without reviewing doc deletions and unrelated changes. Prefer a scoped carry-over that includes app/test/config/doc surfaces needed by formal DEG + ORA + GSEA only.

## 9. Package / open-W / codesign Gate

Recommendation: **yes, rerun before any ReleaseBuild candidate or release handoff.**

Reason:

- Current branch differs from `dev/release-internal-test` in `app/main.py`, `pyproject.toml`, `requirements.txt`, and `config/bioinformatics/package_requirements.yaml`.
- Formal DEG runtime dependency packaging was touched in earlier B9 work.
- B10/B11 add UI, report package, plot artifact, and dependency-detection surfaces that should be validated in packaged app context before release.

Required package gate before release readiness:

```text
git diff --check
python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
python3 -m app.main --smoke-test
python3 scripts/package_app.py --smoke-test
open -W -n dist/BioMedPilot.app --args --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```

If controlled runtime validation is part of the release candidate:

```text
python3 scripts/package_app.py --python "<controlled_venv_python>" --smoke-test
open -W -n dist/BioMedPilot.app --args --bio-formal-deg-runtime-check --bio-formal-deg-runtime-check-output /tmp/biomedpilot_releasebuild_formal_deg_runtime.json
```

This planning step did not rerun packaging because it does not change package/runtime files.

## 10. Excluding `docs/release/ReleaseBuild_handoff_report_20260513.md`

Recommendation: **continue excluding it.**

Current status:

```text
?? docs/release/ReleaseBuild_handoff_report_20260513.md
```

The file is untracked and not part of B11.5 planning. It should remain uncommitted unless a separate release handoff task explicitly asks to include or refresh it.

## 11. Blockers / Major / Minor

Blockers: none for planning.

Major:

- MainLine and `dev/bioinformatics` do not yet contain B10/B11 closure if they are intended to become the active enrichment MVP line.
- `dev/release-internal-test` is behind the current ReleaseBuild candidate if it is still the intended release candidate branch.

Minor:

- Packaging/open-W/codesign have not been rerun after B10/B11 closure in this planning step. This is acceptable for planning, but not for release readiness.

## 12. Final Recommendation

Proceed with one of two routes:

1. **Current branch as ReleaseBuild candidate:** rerun full package/open-W/codesign gates, then create a release-readiness audit.
2. **Scoped carry-over route:** carry B10/B11 enrichment closure to MainLine and/or `dev/release-internal-test`, then rerun formal DEG + ORA + GSEA release gates and package/open-W/codesign.

Do not broaden scope into survival, clinical statistics, full integrated reporting, GSEA phenotype permutation, or rendered figure generation without new task gates.
