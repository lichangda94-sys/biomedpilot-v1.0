# Bioinformatics B16 Legacy Recognition / Acquisition Absorption

Date: 2026-05-21

Workspace: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

Branch: `dev/bioinformatics`

Baseline: `f3f11db docs(bio): add Bioinformatics capability snapshot map`

## Scope

B16 starts absorbing legacy GEO / TCGA / GTEx recognition and acquisition capability through a narrow adapter contract. This stage does not run DEG, ORA, GSEA, KM, Cox, plots, or reports. It does not write formal result index entries and does not treat legacy outputs as formal analysis inputs.

Implemented files:

- `app/bioinformatics/acquisition_adapters/__init__.py`
- `app/bioinformatics/acquisition_adapters/legacy_contract.py`
- `tests/bioinformatics/test_legacy_recognition_adapter.py`
- `tests/bioinformatics/test_geo_acquisition_adapter.py`
- `tests/bioinformatics/test_tcga_gtex_adapter_contract.py`

## Adapter Contract

All B16 adapter manifests use:

- `schema_version=biomedpilot.legacy_acquisition_adapter.v1`
- `source`
- `source_version`
- `legacy_module_reference`
- `input_path_or_query`
- `output_asset_type`
- `provenance`
- `warnings`
- `blockers`
- `checksum`
- `created_at`
- `adapter_id`
- `status`
- `downstream_contract`

The downstream contract is forced to:

- `writes_formal_result=False`
- `ready_for_formal_analysis=False`
- `must_pass_standardization=True`
- `must_pass_b8_resolver=True`
- `allowed_next_layers=["acquisition_manifest", "standardized_asset_candidate", "analysis_input_resolver"]`
- `forbidden_next_layers=["formal_result_index", "formal_plot", "report_ready_package"]`
- `can_fill_tcga_normal_control=False`

## GEO Absorption

Implemented entry:

- `adapt_geo_detection_manifest`

Input:

- legacy detector output from `app.bioinformatics.legacy.geo_processing.detector.detect_dataset`, or an already materialized detection dictionary.

Output:

- `output_asset_type=geo_detection_acquisition_candidate`

Boundary:

- metadata-only legacy detection is blocked.
- probe / ID_REF / unknown matrix level produces a mapping warning.
- no formal result semantics are emitted.
- no report-ready flag is emitted.
- file or text checksum is recorded.

## TCGA Absorption

Implemented entry:

- `adapt_tcga_preview_manifest`

Input:

- current TCGA preview summary or legacy-compatible preview dictionary.

Output:

- `output_asset_type=tcga_gdc_acquisition_manifest_candidate`

Boundary:

- non-ready preview status is blocked.
- missing file manifest entries produce a warning.
- output remains an acquisition candidate and must pass standardization and B8 resolver before analysis.

## GTEx Absorption

Implemented entry:

- `adapt_gtex_preview_manifest`

Input:

- current GTEx preview summary or legacy-compatible preview dictionary.

Output:

- `output_asset_type=gtex_acquisition_manifest_candidate`

Boundary:

- non-ready preview status is blocked.
- GTEx always carries `gtex_must_remain_independent_not_tcga_normal_control`.
- validator blocks any attempt to set `can_fill_tcga_normal_control=True`.
- GTEx cannot be used as default TCGA normal control without a later explicit batch/design gate.

## Formal Promotion Guard

Implemented validator:

- `validate_legacy_acquisition_manifest`

It blocks:

- `output_asset_type` values that look like formal result, plot, or report packages.
- `result_semantics=formal_computed_result` or `report_ready_result`.
- `report_ready_eligible=True`.
- `writes_formal_result` not false.
- `ready_for_formal_analysis` not false.
- missing standardization / B8 resolver requirements.
- GTEx normal-control override.

## Manifest Writer

Implemented writer:

- `write_legacy_acquisition_manifest`

Output path:

- `acquisition/legacy_adapter_manifests/<adapter_id>.json`

The writer only writes adapter manifests. It does not update:

- standardized assets registry.
- repository manifest.
- analysis input repository.
- result index.
- plot artifact registry.
- report-ready package.

## Boundary Acceptance

| Check | Result | Evidence |
| --- | --- | --- |
| legacy output is adapterized before use | Passed | GEO/TCGA/GTEx helper functions produce adapter manifests only. |
| legacy runner cannot write formal result | Passed | Validator requires `writes_formal_result=False` and blocks formal output types. |
| formal result semantics blocked | Passed | Tests forge `formal_computed_result` and validator blocks it. |
| report-ready blocked | Passed | Validator blocks `report_ready_eligible=True`. |
| GTEx normal-control shortcut blocked | Passed | GTEx contract forces `can_fill_tcga_normal_control=False`. |
| B8 resolver remains required | Passed | Downstream contract forces `must_pass_b8_resolver=True`. |

## Current Limitations

- This stage does not yet convert adapter manifests into standardized repository assets.
- This stage does not yet add UI rows for legacy adapter manifests.
- This stage does not run live GEO/TCGA/GTEx acquisition.
- ORA/GSEA controlled runtime remains absent in this branch, as recorded in B15.

## Test Record

Initial targeted validation:

- `python3 -m pytest tests/bioinformatics/test_legacy_recognition_adapter.py tests/bioinformatics/test_geo_acquisition_adapter.py tests/bioinformatics/test_tcga_gtex_adapter_contract.py -q` -> 7 passed.

Final validation:

- `git diff --check` -> passed.
- `python3 -m pytest tests/bioinformatics -q -k "legacy or adapter or geo or tcga or gtex or recognition or standardization or resolver"` -> 213 passed, 200 deselected.
- `python3 -m pytest tests/bioinformatics -q` -> 413 passed.
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` -> 176 passed.
- `python3 -m app.main --smoke-test` -> passed, `git_head=f3f11db`, `pyside6_available=True`.

## Recommendation

Proceed next to a B16.1 standardized asset bridge only after this adapter layer is accepted. That bridge should read `acquisition/legacy_adapter_manifests/*.json` and create standardized asset candidates, still without formal analysis execution.
