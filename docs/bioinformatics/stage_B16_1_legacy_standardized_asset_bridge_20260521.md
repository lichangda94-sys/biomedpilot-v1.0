# Bioinformatics B16.1 Legacy Standardized Asset Candidate Bridge

Date: 2026-05-21

Workspace: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

Branch: `dev/bioinformatics`

Baseline: `199e7c5 add Bioinformatics legacy acquisition adapters`

## Scope

B16.1 bridges B16 legacy acquisition adapter manifests into standardized asset candidates. It is still not a formal standardization execution stage and does not register analysis inputs or formal results.

Implemented files:

- `app/bioinformatics/acquisition_adapters/standardized_bridge.py`
- updated `app/bioinformatics/acquisition_adapters/__init__.py`
- `tests/bioinformatics/test_legacy_standardized_asset_bridge.py`

## Output Contract

Input:

- `acquisition/legacy_adapter_manifests/*.json`

Output:

- `standardized_data/asset_candidates/legacy_acquisition_asset_candidates.json`

The output bundle uses:

- `schema_version=biomedpilot.legacy_standardized_asset_candidate_bundle.v1`
- `candidate_count`
- `manifest_count`
- `manifests`
- `candidates`
- `candidate_validations`
- `downstream_contract`

The bundle downstream contract forces:

- `writes_repository_manifest=False`
- `writes_analysis_input_repository=False`
- `writes_result_index=False`
- `ready_for_formal_analysis=False`
- `must_pass_standardization_validation=True`
- `must_pass_b8_resolver=True`

## Candidate Contract

Each candidate uses:

- `schema_version=biomedpilot.legacy_standardized_asset_candidate.v1`
- `candidate_id`
- `source`
- `source_adapter_id`
- `source_manifest_path`
- `source_manifest_checksum`
- `asset_type`
- `asset_role`
- `path_or_query`
- `provenance`
- `warnings`
- `blockers`
- `validation_status`
- `formal_analysis_ready=False`
- `result_semantics=not_a_result`
- `report_ready_eligible=False`
- `can_fill_tcga_normal_control=False`
- `next_required_gates=["standardization_validation", "b8_analysis_input_resolver"]`

## Source Mapping

GEO:

- candidate expression files -> `geo_expression_matrix_candidate`
- candidate metadata files -> `geo_sample_metadata_candidate`
- candidate platform annotation files -> `geo_platform_annotation_candidate`
- metadata-only / blocked detection remains blocked and cannot become formal-ready

TCGA:

- GDC expression file manifest entries -> `tcga_expression_matrix_candidate`
- clinical-looking file manifest entries -> `tcga_clinical_metadata_candidate`
- generic GDC entries -> `tcga_gdc_file_candidate`

GTEx:

- expression entries -> `gtex_expression_matrix_candidate`
- sample/annotation entries -> `gtex_sample_metadata_candidate`
- all candidates retain `can_fill_tcga_normal_control=False`

## Formal Promotion Guard

Implemented validator:

- `validate_legacy_standardized_asset_candidate`

It blocks:

- `formal_analysis_ready=True`
- `result_semantics=formal_computed_result` or `report_ready_result`
- `report_ready_eligible=True`
- missing `standardization_validation` gate
- missing `b8_analysis_input_resolver` gate
- GTEx candidate normal-control override

## Boundary Acceptance

| Check | Result | Evidence |
| --- | --- | --- |
| Reads B16 adapter manifests only | Passed | Bridge reads `acquisition/legacy_adapter_manifests/*.json`. |
| Writes candidate bundle only | Passed | Output is limited to `standardized_data/asset_candidates/legacy_acquisition_asset_candidates.json`. |
| Does not write repository manifest | Passed | Tests assert `standardized_data/repositories/repository_manifest.json` is absent after bridge write. |
| Does not write analysis input repository | Passed | Tests assert `standardized_data/repositories/analysis_input_repository` is absent after bridge write. |
| Does not write result index | Passed | Bundle contract sets `writes_result_index=False`. |
| Formal promotion blocked | Passed | Forged formal candidate is blocked by validator. |
| GTEx normal-control shortcut blocked | Passed | GTEx candidates keep `can_fill_tcga_normal_control=False`. |

## Limitations

- Candidates are not yet materialized repository assets.
- Candidates are not visible in the UI.
- No live GEO / TCGA / GTEx fetch is run.
- No formal DEG / ORA / GSEA / KM / Cox / plot / report capability is added.

## Test Record

Initial validation:

- `python3 -m pytest tests/bioinformatics/test_legacy_standardized_asset_bridge.py tests/bioinformatics/test_legacy_recognition_adapter.py tests/bioinformatics/test_geo_acquisition_adapter.py tests/bioinformatics/test_tcga_gtex_adapter_contract.py -q` -> 11 passed.
- `python3 -m pytest tests/bioinformatics -q -k "legacy or adapter or geo or tcga or gtex or recognition or standardization or resolver"` -> 217 passed, 200 deselected.

Final validation:

- `git diff --check` -> passed.
- `python3 -m pytest tests/bioinformatics -q` -> 417 passed.
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` -> 176 passed.
- `python3 -m app.main --smoke-test` -> passed, `git_head=199e7c5`, `pyside6_available=True`.

## Recommendation

Proceed next to B16.2 only if the goal is to materialize selected candidates into real standardized repository assets. B16.2 must still require explicit standardization validation and must not let candidate bundles directly feed formal analysis.
