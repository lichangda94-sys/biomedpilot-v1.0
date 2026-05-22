# Bioinformatics B16.4 Legacy Asset Selection / Validation Gate

Date: 2026-05-21

Workspace: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

Branch: `dev/bioinformatics`

Baseline: `b6c1e3b add Bioinformatics legacy repository merge gate`

## Scope

B16.4 adds explicit asset selection for legacy-derived repository assets. It lets a user-confirmed selection write default asset choices back to `repository_manifest.json`, but it still does not create analysis input repository packages, result index entries, plot artifacts, or report-ready packages.

Implemented files:

- `app/bioinformatics/acquisition_adapters/selection_gate.py`
- updated `app/bioinformatics/acquisition_adapters/__init__.py`
- `tests/bioinformatics/test_legacy_asset_selection_gate.py`

## Selection Manifest

Output path:

- `standardized_data/asset_candidates/legacy_asset_selection_manifest.json`

Manifest schema:

- `schema_version=biomedpilot.legacy_asset_selection_manifest.v1`
- `confirmed_by_user`
- `selected_assets`
- `downstream_gate_preview`
- `formal_analysis_ready=False`
- `ready_for_formal_analysis=False`
- `result_semantics=not_a_result`
- `report_ready_eligible=False`

Supported selections:

- expression
- sample metadata
- feature annotation
- clinical metadata
- group design

## Repository Manifest Update

When structural selection validation passes, B16.4 updates:

- `repository_manifest.default_asset_selection`
- selected assets' `default_selected=True`
- selected assets' `legacy_selection_confirmed=True`
- `source_state.legacy_asset_selection=True`
- `legacy_asset_selection_contract`

It does not update:

- `standardized_data/repositories/analysis_input_repository/*`
- `results/summaries/result_index.json`
- plot artifact registry
- report-ready package

## Two-Layer Validation

Selection blockers prevent repository manifest update:

- missing user confirmation.
- selected asset not found.
- selected asset type/role mismatch.
- selected asset has formal/result/report-ready fields.
- selection contract tries to write analysis input repository or result index.

Downstream blockers do not prevent saving a valid default selection, but they keep formal analysis blocked:

- missing expression asset selection.
- missing sample metadata selection.
- missing group design selection.
- unknown / unsupported expression value type.
- probe / ID_REF / unknown gene ID mapping without confirmed feature annotation.
- GTEx expression selected as TCGA normal-control-like input.
- clinical selected without expression.

## Resolver Boundary

After selection is written, B8 resolver can use the selected default expression asset. This removes the global multiple-expression-candidate ambiguity, but it does not imply formal analysis readiness.

Formal DEG still requires:

- sample metadata.
- group design.
- DEG-ready matrix gate.
- dependency gate.
- parameter and confirmation gates.
- result schema gate.

Survival/clinical still requires:

- valid expression and clinical assets.
- outcome gate.
- clinical variable gate.
- KM/Cox parameter and confirmation gates.

## Boundary Acceptance

| Check | Result | Evidence |
| --- | --- | --- |
| User confirmation required | Passed | Unconfirmed selection is blocked and does not update repository manifest. |
| Default expression selection written | Passed | Test confirms `repository_manifest.default_asset_selection.expression` is set. |
| Multiple expression ambiguity resolved | Passed | Resolver no longer reports `multiple_candidate_matrices_without_default_selection` after selection. |
| Formal DEG remains blocked | Passed | Resolver DEG package remains blocked by missing group design. |
| Analysis input repository not written | Passed | Tests assert `analysis_input_repository` is absent. |
| Result index not written | Passed | Tests assert `results/summaries/result_index.json` is absent. |
| Formalish asset blocked | Passed | Asset with formal fields is blocked by selection validation. |
| GTEx normal-control boundary retained | Passed | Selection records GTEx downstream blocker and resolver keeps GTEx DEG/survival blockers. |

## Current Limitations

- No UI panel is added for selection.
- No automatic group design generation is added.
- No biological normalization, sample alignment, probe mapping, or formal DEG-ready package is created.
- No formal DEG / ORA / GSEA / KM / Cox / plot / report capability is added.

## Test Record

Initial validation:

- `python3 -m pytest tests/bioinformatics/test_legacy_asset_selection_gate.py tests/bioinformatics/test_legacy_repository_manifest_merge_gate.py tests/bioinformatics/test_legacy_candidate_materialization_gate.py tests/bioinformatics/test_legacy_standardized_asset_bridge.py tests/bioinformatics/test_legacy_recognition_adapter.py tests/bioinformatics/test_geo_acquisition_adapter.py tests/bioinformatics/test_tcga_gtex_adapter_contract.py -q` -> 25 passed.
- `python3 -m pytest tests/bioinformatics -q -k "legacy or adapter or geo or tcga or gtex or recognition or standardization or resolver"` -> 231 passed, 200 deselected.

Final validation:

- `git diff --check` -> passed.
- `python3 -m pytest tests/bioinformatics -q` -> 431 passed.
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` -> 176 passed.
- `python3 -m app.main --smoke-test` -> passed, `git_head=b6c1e3b`, `pyside6_available=True`.

## Recommendation

Proceed next to B16.5 if the priority is UI exposure for the B16 adapter/candidate/materialization/merge/selection chain. If the priority is analysis readiness, the next stage should add a separate group design and DEG-ready validation bridge, still without running formal DEG.
