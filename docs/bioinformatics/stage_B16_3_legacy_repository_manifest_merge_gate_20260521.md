# Bioinformatics B16.3 Legacy Repository Manifest Merge Gate

Date: 2026-05-21

Workspace: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

Branch: `dev/bioinformatics`

Baseline: `c7f4ade add Bioinformatics legacy candidate materialization gate`

## Scope

B16.3 merges validated materialized legacy assets into the main standardized repository manifest. This is the first B16 step where B8 resolver can see legacy-derived assets, but the assets remain not analysis-ready and not formal-ready.

Implemented files:

- `app/bioinformatics/acquisition_adapters/repository_merge.py`
- updated `app/bioinformatics/acquisition_adapters/__init__.py`
- `tests/bioinformatics/test_legacy_repository_manifest_merge_gate.py`

## Input And Output

Input:

- `standardized_data/asset_candidates/legacy_materialized_assets_manifest.json`

Outputs:

- `standardized_data/repositories/repository_manifest.json`
- `standardized_data/repositories/validation_report.json`
- `standardized_data/repositories/asset_lineage.jsonl`
- `standardized_data/asset_candidates/legacy_repository_manifest_merge.json`

Explicitly not written:

- `standardized_data/repositories/analysis_input_repository/*`
- `results/summaries/result_index.json`
- plot artifact registry
- report-ready package

## Merge Plan Contract

`plan_legacy_repository_manifest_merge` records:

- source materialization manifest
- selected materialized asset IDs
- normalized merge assets
- downstream contract
- validation result

The downstream contract forces:

- `writes_repository_manifest=True`
- `writes_validation_report=True`
- `writes_asset_lineage=True`
- `writes_analysis_input_repository=False`
- `writes_result_index=False`
- `ready_for_formal_analysis=False`
- `requires_b8_resolver_after_merge=True`

## Asset Normalization

Legacy-specific materialized asset types are mapped to B8-visible standardized asset types:

- `geo_expression_matrix` -> `expression_matrix`
- `tcga_expression_matrix` -> `tcga_expression_matrix`
- `gtex_expression_matrix` -> `gtex_expression_matrix`
- metadata roles -> `sample_metadata` / `tcga_sample_metadata` / `gtex_sample_metadata`
- feature roles -> `platform_annotation`
- clinical roles -> `clinical_metadata` / `tcga_clinical_metadata`

The merge record preserves the legacy type in `legacy_asset_type`.

## Formal Boundary

Every merged asset keeps:

- `analysis_ready=False`
- `formal_analysis_ready=False`
- `result_semantics=not_a_result`
- `report_ready_eligible=False`
- `default_selected=False`
- `consumable_by=[]`
- `biological_normalization_performed=False`

The merge gate does not create analysis input packages. B8 resolver may see these assets, but downstream DEG/survival/etc. gates still block until required metadata, group design, value type, gene ID mapping and task-specific gates pass.

## Validator

`validate_legacy_repository_manifest_merge_plan` blocks:

- analysis input repository writes.
- result index writes.
- formal-ready merge plan.
- `analysis_ready=True` on merge assets.
- `formal_analysis_ready=True`.
- formal result semantics.
- report-ready eligibility.
- missing asset ID/path.

## Boundary Acceptance

| Check | Result | Evidence |
| --- | --- | --- |
| Repository manifest written | Passed | Test asserts `repository_manifest.json` exists after merge. |
| Validation report written | Passed | Test asserts `validation_report.json` exists after merge. |
| Lineage written | Passed | Test asserts `asset_lineage.jsonl` exists after merge. |
| Analysis input repository not written | Passed | Test asserts `analysis_input_repository` is absent. |
| Result index not written | Passed | Test asserts `results/summaries/result_index.json` is absent. |
| Resolver sees merged asset | Passed | Resolver returns a DEG package with expression asset from merged repository. |
| Formal DEG remains blocked | Passed | Resolver DEG package remains blocked by missing sample/group and/or value/gene gates. |
| GTEx normal-control boundary retained | Passed | Resolver blocks GTEx auto normal-control in DEG and survival packages. |
| Formal promotion blocked | Passed | Forged merge plan and asset formal fields are blocked. |

## Current Limitations

- This stage does not write `analysis_input_repository` packages.
- This stage does not mark assets as analysis-ready.
- This stage does not choose default assets.
- This stage does not perform biological normalization, probe collapse, batch correction, or TCGA+GTEx merge.
- This stage does not enable formal DEG / ORA / GSEA / KM / Cox / plot / report execution.

## Test Record

Initial validation:

- `python3 -m pytest tests/bioinformatics/test_legacy_repository_manifest_merge_gate.py tests/bioinformatics/test_legacy_candidate_materialization_gate.py tests/bioinformatics/test_legacy_standardized_asset_bridge.py tests/bioinformatics/test_legacy_recognition_adapter.py tests/bioinformatics/test_geo_acquisition_adapter.py tests/bioinformatics/test_tcga_gtex_adapter_contract.py -q` -> 21 passed.
- `python3 -m pytest tests/bioinformatics -q -k "legacy or adapter or geo or tcga or gtex or recognition or standardization or resolver"` -> 227 passed, 200 deselected.

Final validation:

- `git diff --check` -> passed.
- `python3 -m pytest tests/bioinformatics -q` -> 427 passed.
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` -> 176 passed.
- `python3 -m app.main --smoke-test` -> passed, `git_head=c7f4ade`, `pyside6_available=True`.

## Recommendation

Proceed next to B16.4 only if the goal is to add explicit user selection and validation for merged legacy assets. B16.4 should choose defaults and create resolver-visible readiness only after value type, gene ID mapping, sample metadata and group design gates are explicit. It still should not run formal analysis.
