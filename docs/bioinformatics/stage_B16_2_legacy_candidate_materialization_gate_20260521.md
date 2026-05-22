# Bioinformatics B16.2 Legacy Candidate Materialization Gate

Date: 2026-05-21

Workspace: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

Branch: `dev/bioinformatics`

Baseline: `5906ebd add Bioinformatics legacy standardized asset bridge`

## Scope

B16.2 materializes selected B16.1 legacy standardized asset candidates into isolated repository files. It is a materialization gate only. It does not merge those assets into the main repository manifest and does not expose them to the B8 resolver.

Implemented files:

- `app/bioinformatics/acquisition_adapters/materialization.py`
- updated `app/bioinformatics/acquisition_adapters/__init__.py`
- `tests/bioinformatics/test_legacy_candidate_materialization_gate.py`

## Input And Output

Input:

- `standardized_data/asset_candidates/legacy_acquisition_asset_candidates.json`

Outputs:

- materialized files under role-specific repository folders, such as:
  - `standardized_data/repositories/expression_repository/`
  - `standardized_data/repositories/sample_metadata_repository/`
  - `standardized_data/repositories/feature_annotation_repository/`
  - `standardized_data/repositories/clinical_repository/`
  - `standardized_data/repositories/legacy_acquisition_repository/`
- `standardized_data/asset_candidates/legacy_materialized_assets_manifest.json`
- `standardized_data/asset_candidates/legacy_materialized_asset_lineage.jsonl`

Explicitly not written:

- `standardized_data/repositories/repository_manifest.json`
- `standardized_data/repositories/analysis_input_repository/*`
- `results/summaries/result_index.json`
- plot artifact registry
- report-ready package

## Materialization Plan Contract

`build_legacy_candidate_materialization_plan` records:

- selected candidate IDs
- source candidate bundle
- target repository paths
- validation blockers and warnings
- downstream contract

The downstream contract forces:

- `writes_repository_files=True`
- `writes_repository_manifest=False`
- `writes_analysis_input_repository=False`
- `writes_result_index=False`
- `ready_for_formal_analysis=False`
- `requires_later_repository_manifest_merge=True`
- `requires_b8_resolver_after_merge=True`

## Materialized Asset Contract

Materialized assets include:

- `asset_id`
- `asset_type`
- `asset_role`
- `repository`
- `path`
- `source_file`
- `source_candidate_id`
- `source_adapter_id`
- `source_manifest_path`
- checksum and size
- warnings / blockers
- `analysis_ready=False`
- `formal_analysis_ready=False`
- `result_semantics=not_a_result`
- `report_ready_eligible=False`
- `materialize_strategy=legacy_candidate_materialization_gate`
- `biological_normalization_performed=False`
- next required gates:
  - `repository_manifest_merge`
  - `standardization_validation`
  - `b8_analysis_input_resolver`

## File Handling

- Existing local source files are copied into the isolated repository folder.
- Missing source files become sidecar-only JSON records with `candidate_source_path_not_found_sidecar_only`.
- Blocked candidates are not materialized as assets.

## Formal Promotion Guard

`validate_legacy_candidate_materialization_plan` blocks:

- writing repository manifest
- writing analysis input repository
- writing result index
- `ready_for_formal_analysis=True`
- plan items with `formal_analysis_ready=True`
- formal result semantics
- writing analysis input repository from an item

## Boundary Acceptance

| Check | Result | Evidence |
| --- | --- | --- |
| Candidate validation required | Passed | Blocked candidate test does not materialize an asset. |
| Existing files are copied | Passed | Test copies a GEO expression matrix candidate and verifies contents. |
| Missing files are sidecar-only | Passed | Test writes sidecar JSON and keeps `formal_analysis_ready=False`. |
| Main repository manifest not written | Passed | Test asserts `repository_manifest.json` is absent. |
| Analysis input repository not written | Passed | Test asserts `analysis_input_repository` is absent. |
| Result index not written | Passed | Test asserts `results/summaries/result_index.json` is absent. |
| Formal promotion blocked | Passed | Forged plan/candidate formal fields are blocked. |

## Current Limitations

- Materialized candidates are not visible to B8 resolver until a later explicit repository manifest merge stage.
- No UI panel is added for candidate materialization.
- No biological normalization or probe collapse is performed.
- No formal DEG / ORA / GSEA / KM / Cox / plot / report capability is added.

## Test Record

Initial validation:

- `python3 -m pytest tests/bioinformatics/test_legacy_candidate_materialization_gate.py tests/bioinformatics/test_legacy_standardized_asset_bridge.py tests/bioinformatics/test_legacy_recognition_adapter.py tests/bioinformatics/test_geo_acquisition_adapter.py tests/bioinformatics/test_tcga_gtex_adapter_contract.py -q` -> 16 passed.
- `python3 -m pytest tests/bioinformatics -q -k "legacy or adapter or geo or tcga or gtex or recognition or standardization or resolver"` -> 222 passed, 200 deselected.

Final validation:

- `git diff --check` -> passed.
- `python3 -m pytest tests/bioinformatics -q` -> 422 passed.
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` -> 176 passed.
- `python3 -m app.main --smoke-test` -> passed, `git_head=5906ebd`, `pyside6_available=True`.

## Recommendation

Proceed next to B16.3 only if the goal is explicit repository manifest merge. B16.3 must remain separate from resolver execution and formal analysis activation. It should merge only validated materialized assets into `repository_manifest.json`, then require B8 resolver tests before any downstream analysis gate can see them.
