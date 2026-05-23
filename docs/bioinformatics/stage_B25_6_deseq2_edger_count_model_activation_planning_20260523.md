# B25.6 DESeq2 / edgeR Count-Model Activation Planning

Date: 2026-05-23

## Scope

B25.6 defines the activation plan for DESeq2 and edgeR after the limma Rscript
MVP closure. This stage is planning and gate hardening only.

It does not execute DESeq2 or edgeR, does not register DESeq2/edgeR formal
results, does not generate plot/report-ready artifacts, and does not change
GSEA, survival or clinical analysis behavior.

## Implemented Contract Surface

Added a count-model activation plan layer:

- `app/bioinformatics/deg_engine/r_count_model_planning.py`
- `build_r_count_model_activation_plan(method, ...)`
- `build_r_count_model_activation_plans(...)`

The plan covers:

- resolver and DEG-ready package requirement;
- raw integer count matrix requirement;
- blocked TPM / FPKM / normalized / log expression value types;
- count-model design preflight;
- detect-only R/Bioconductor/package dependency snapshot;
- method-specific parameter confirmation requirement;
- method-specific Rscript execution adapter requirement;
- method-specific output schema requirement;
- result index v2 registration requirement.

## UI Gate Behavior

Analysis Center now exposes B25.6 count-model activation planning rows for:

- `deseq2`
- `edger`

Action rows are present but disabled:

- `formal_deg_deseq2_rscript`
- `formal_deg_edger_rscript`

The disabled reason includes:

- `b25_6_count_model_planning_only:<method>`;
- `<method>_rscript_execution_adapter_not_implemented`;
- `<method>_parameter_confirmation_contract_not_implemented`;
- `<method>_result_registration_handoff_not_implemented`;
- any resolver, value-type, count matrix, design preflight or runtime gate blockers.

The capability map marks DESeq2 and edgeR as
`b25_6_count_model_activation_planning` and keeps:

- `formal_execution_enabled=False`;
- `can_display_as_completed=False`;
- no result index write;
- no `formal_computed_result` semantics.

## Handoff Boundary Update

`build_r_deg_external_handoff_plan("DESeq2")` and
`build_r_deg_external_handoff_plan("edgeR")` now report B25.6 planning-only
blockers instead of the previous "deferred until after limma acceptance"
blocker. limma acceptance is complete; the remaining blockers are method-specific
activation work.

## Not Implemented

- No DESeq2 Rscript adapter.
- No edgeR Rscript adapter.
- No DESeq2/edgeR user parameter confirmation manifest writer.
- No DESeq2/edgeR formal result registration handoff.
- No DESeq2/edgeR result review UI.
- No DESeq2/edgeR plot/report-ready package.
- No auto-install of R, Bioconductor, DESeq2 or edgeR.

## Validation Commands

```bash
git diff --check
python3 -m py_compile app/bioinformatics/deg_engine/r_count_model_planning.py app/bioinformatics/analysis_ui/state.py app/bioinformatics/analysis_ui/action_rules.py app/bioinformatics/analysis_ui/capability_map.py app/bioinformatics/deg_engine/r_backend_handoff.py
python3 -m pytest -q tests/bioinformatics/test_r_count_model_planning.py tests/bioinformatics/test_r_deg_external_handoff.py tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_ui_action_rules.py
python3 -m pytest tests/bioinformatics -q -k "r_deg or r_limma or count_model or multifactor or analysis_ui or formal_deg"
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or deg_config or results_browser"
python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
python3 -m app.main --smoke-test
python3 scripts/package_app.py --smoke-test
open -W -n dist/BioMedPilot.app --args --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```

## Validation Results

Baseline before this B25.6 commit: `c667e42`.

- `git diff --check`: passed.
- `python3 -m py_compile app/bioinformatics/deg_engine/r_count_model_planning.py app/bioinformatics/analysis_ui/state.py app/bioinformatics/analysis_ui/action_rules.py app/bioinformatics/analysis_ui/capability_map.py app/bioinformatics/deg_engine/r_backend_handoff.py app/bioinformatics/deg_engine/__init__.py`: passed.
- `python3 -m pytest -q tests/bioinformatics/test_r_count_model_planning.py tests/bioinformatics/test_r_deg_external_handoff.py tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_ui_action_rules.py`: 31 passed.
- `python3 -m pytest tests/bioinformatics -q -k "r_deg or r_limma or count_model or multifactor or analysis_ui or formal_deg"`: 83 passed, 600 deselected.
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or deg_config or results_browser"`: 18 passed, 98 deselected.
- `python3 -m pytest tests/bioinformatics -q`: 683 passed, 1 existing scipy precision warning.
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`: 273 passed.
- `python3 -m app.main --smoke-test`: passed, source launch, `git_head=c667e42`.
- `python3 scripts/package_app.py --smoke-test`: passed, packaged local Python launcher, `git_head=c667e42`, ad-hoc signed.
- `open -W -n dist/BioMedPilot.app --args --smoke-test`: passed.
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`: passed.

## ReleaseBuild Recommendation

ReleaseBuild can expose DESeq2/edgeR as planned count-model methods with clear
disabled reasons. It should not advertise DESeq2/edgeR as implemented execution
capabilities until a later scoped activation stage adds method-specific
parameter confirmation, Rscript adapters, output validation, result review and
package/open-W/codesign validation.
