# Stage B5.8A Legacy GEO Parser Capability Audit

Date: 2026-05-14

Scope: light read-only audit for legacy GEO SOFT / Series Matrix parsing capability. Runtime code was not changed.

## Search Scope

Audited current Bioinformatics worktree:

- `app/bioinformatics/**`
- `tests/bioinformatics/**`
- `docs/bioinformatics/**`

Audited read-only sibling source trees:

- `/Users/changdali/Developer/biomedpilot v1.0/MainLine/app/**`
- `/Users/changdali/Developer/biomedpilot v1.0/Integration/app/**`
- `/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild/app/**`

Search terms included `GEO`, `SOFT`, `Series Matrix`, `series_matrix`, `family.soft`, `matrix_table_begin`, `matrix_table_end`, `Sample_characteristics`, `Sample_geo_accession`, `Platform`, `ID_REF`, `GPL`, `GSE`, `geo_parser`, and `soft_parser`.

Notes:

- `dist/*.app` bundle contents were not used as evidence. A few source-like paths were visible during file discovery, but the audit did not reverse, unpack, or rely on desktop app bundles.
- Validation logs and generated reports under sibling trees were treated as historical output only, not parser source.

## Relevant Files Found

### Current Bioinformatics runtime

- `app/bioinformatics/project_recognition.py`
  - Active recognition runner.
  - Defines `geo_soft_container` and `geo_series_matrix_container`.
  - `_classify_geo_soft()` and `_scan_geo_soft()` detect GEO SOFT container markers such as `^SAMPLE`, `!Sample_title`, `!Sample_characteristics`, `^PLATFORM`, `!platform_table_begin`, `!sample_table_begin`, `ID_REF`, and `VALUE`.
  - `_classify_geo_series_matrix()` and `_scan_geo_series_matrix()` detect Series Matrix markers such as `!series_matrix_table_begin`, `!series_matrix_table_end`, `ID_REF`, GSM sample columns, sample titles, characteristics, platform id, and organism.
  - These scanners create recognition roles/assets and content-profile evidence, but do not materialize a full expression matrix or normalized sample metadata table.

- `app/bioinformatics/services/geo_metadata_profile_service.py`
  - Current metadata-profile helper.
  - `_parse_family_soft()` and `_parse_series_matrix()` extract title, summary, design, platform, organism, sample titles, sample characteristics, sample records, and candidate comparisons.
  - `_parse_series_matrix()` stops at `!series_matrix_table_begin`; it does not parse the expression matrix block into a matrix artifact.

### Current legacy code

- `app/bioinformatics/legacy/geo_tool/geo_pipeline/process.py`
  - Clear full-family-SOFT processor built on `GEOparse`.
  - `load_full_family_soft()` uses `GEOparse.get_GEO(filepath=...)` and rejects `.txt`, so it is not a Series Matrix parser.
  - Extracts phenotype data, infers group column, builds expression matrix with `gse.pivot_samples(values="VALUE", index="ID_REF")`, inspects tables, detects GPL gene-symbol columns, annotates probe expression, and can aggregate to gene level.
  - Writes legacy CSV/JSON outputs such as phenotype, group summary, raw/clean probe expression, optional annotated and gene-level expression, and run summary.

- `app/bioinformatics/legacy/process_geo_family_soft.py`
  - Compatibility-style wrapper around the same GEOparse object model.
  - Documentation states it reuses GEOparse GSE/GPL/GSM objects, targets local full family SOFT or existing GSE object input, and avoids rebuilding GEO object logic.
  - Also rejects `.txt` input and is therefore not a Series Matrix parser.

- `app/bioinformatics/legacy/geo_pipeline/process.py`
  - Legacy pipeline variant with the same GEOparse family-SOFT shape.

- `app/bioinformatics/legacy/geo_processing/download_validator.py`
  - Robust local file scorer / validator.
  - Detects GEO containers, family SOFT metadata sources, sample annotations, platform hints, expression payload candidates, raw files, junk files, and differential-result tables.
  - It supports semantic classification and strategy selection, but is not a parser that emits current recognition assets.

- `app/bioinformatics/legacy/geo_processing/detector/matrix_classifier.py`
  - Tabular matrix classifier for supplementary tables.
  - Distinguishes likely expression matrices, probe/gene/transcript level, raw counts/log/intensity-like values, metadata tables, and differential-result tables.

- `app/bioinformatics/legacy/geo_processing/detector/dataset_detector.py`
  - Aggregates validator findings and recommends strategies such as `SERIES_MATRIX_FIRST`, `SOFT_METADATA_PLUS_SUPP_MATRIX`, and `METADATA_ONLY`.
  - This is workflow classification rather than parsing.

### Tests

- `tests/bioinformatics/test_workflow_adapters.py`
  - Current active tests assert GEO family SOFT and Series Matrix are recognized as multi-role containers and can register standardization assets from detected roles.
  - The tests cover marker-based recognition, not extraction of full matrices from SOFT or Series Matrix.

- `app/bioinformatics/legacy/tests/test_geo_detector.py`
  - Legacy detector tests cover normal Series Matrix strategy, family.soft-only metadata strategy, supplementary matrix-first strategy, probe-level hints, and diff-result suppression.
  - These tests validate classification decisions, not a full parser output contract.

- `app/bioinformatics/legacy/tests/test_download_validator.py`
  - Legacy validator coverage exists for file scoring and dataset validation behavior.

### Sibling source trees

MainLine, Integration, and ReleaseBuild contain similar legacy GEO source under `app/bioinformatics/legacy/**`.

Additional sibling service code was found in MainLine and ReleaseBuild:

- `app/bioinformatics/services/geo_differential_expression_runner.py`
- `app/bioinformatics/services/correlation_runner.py`

Those files include `_geo_series_matrix_rows()` helpers that read rows between `!series_matrix_table_begin` and `!series_matrix_table_end`. This is a useful row-reader clue, but it belongs to testing-level DEG/correlation services and does not provide a reusable current recognition parser contract.

## Capability Depth

| Format | Existing capability | Depth judgment |
| --- | --- | --- |
| `family.soft` / full GEO family SOFT | Legacy GEOparse processors can load GSE objects, extract phenotype table, infer group column, build probe expression matrix via `pivot_samples`, inspect GPL/GSM tables, detect gene symbol columns, annotate probes, and aggregate to gene level. Current recognition only scans markers and emits container/assets. | Legacy capability is deep, but not connected to current recognition. |
| `series_matrix.txt` | Current recognition scans header/table markers and sample metadata. `geo_metadata_profile_service` parses metadata before matrix block. Legacy detector can classify Series Matrix as preferred expression source. Sibling services can read table rows. | No complete reusable parser found that emits expression matrix plus sample metadata in the current recognition schema. Capability is shallow-to-moderate and fragmented. |
| `series_matrix.txt.gz` | Active recognition and legacy detector paths include gzip-safe open helpers and tests use gzipped Series Matrix fixtures. | Detection/classification support exists; full parser support remains fragmented. |
| GEO supplementary table | Legacy `matrix_classifier.py` and current tabular profilers can classify expression-like, metadata-like, probe/gene-level, and diff-result-like tables. | Useful classification helpers exist, but this is not SOFT/Series Matrix parsing. |
| Platform annotation | Legacy GEOparse SOFT processor can use GPL tables and detect gene-symbol columns. Current Series Matrix recognition only emits platform reference hints; current SOFT recognition marks platform annotation by markers. | Deep legacy SOFT capability; shallow current recognition capability. |
| Phenotype/group inference | Legacy SOFT processor has group-column inference from phenotype data. Current recognition has preview-only group hints and metadata profile candidate comparisons. | Legacy SOFT path is deeper, but needs adapter/test work before reuse. |
| Species/gene id inference | `geo_metadata_profile_service` extracts organism; legacy classifier distinguishes probe/gene/transcript-like ids; legacy SOFT processor can map probe to gene via GPL. | Partial current support, deeper legacy SOFT support. |

## Is There Capability Regression?

Yes, but it differs by format.

For full `family.soft`, there is a real regression in workflow integration. The old GEOparse processor can do more than container detection: phenotype extraction, expression matrix creation, platform annotation, and gene-level aggregation. The current recognition runner does not call that processor and therefore treats SOFT mainly as a multi-role container with evidence markers.

For Series Matrix, the evidence does not show an old complete parser that was simply left unplugged. The old code mostly classified Series Matrix files, parsed metadata headers, or read raw rows for isolated services. Current recognition already performs similar container/table-marker recognition. A proper Series Matrix parser still appears to be missing rather than merely disconnected.

## Regression Cause Judgment

- Full family SOFT: old capability exists, but it was not migrated or not wired into the current recognition workflow.
- Series Matrix: old capability itself appears shallow and split across detector, metadata profile, and service-specific row readers.
- Dependency status: `GEOparse`, `pandas`, and `numpy` are available in the current local Python environment (`GEOparse 2.0.4`, `pandas 3.0.2`, `numpy 2.4.4`). This reduces dependency risk for a scoped SOFT carry-over, but packaging/runtime dependency policy still needs confirmation before productizing it.
- Test coverage: legacy tests cover detection/strategy behavior; current tests cover container recognition. No current test asserts full SOFT expression extraction or full Series Matrix parser output.
- Architecture mismatch: legacy processors write CSV/JSON files and assume their own pipeline outputs. Current recognition uses `RecognitionClassification`, `detected_assets`, readiness summaries, and standardization registry handoff. A direct drop-in migration would not fit safely without an adapter.

## Can It Connect to Current Recognition Runner?

Potentially, but not as a wholesale migration.

Safe reuse shape:

- Keep `display_name` and `source_files` semantics from B5.6 untouched.
- Add a scoped parser adapter that receives the selected source path(s), reads the file in place, and maps extracted evidence into current recognition assets/content profile.
- Preserve B5 imported DEG semantics by keeping differential-result tables separate from expression matrices and not treating imported DEG results as raw expression input.
- Preserve report safety by emitting recognition evidence only, not running new DEG execution or report generation.

Risky reuse shape:

- Calling legacy pipeline entry points directly from recognition, because they write legacy output files and have their own workflow assumptions.
- Reusing dataset-level validators as recognition truth without mapping their result model to current assets.
- Treating `display_name` or inferred dataset name as a file list.

## Reuse Recommendation

Recommendation is split by file type:

1. Full family SOFT: recommend B5.8B scoped carry-over.
   - The old entry point is clear.
   - The parser depth is meaningful.
   - Optional dependency availability is confirmed locally.
   - Reuse should be adapter-based and test-first, not a direct workflow transplant.
   - Minimum carry-over target: sample metadata, phenotype candidate fields, expression matrix evidence, platform/GPL annotation evidence, and row/column summary in the current recognition schema.

2. Series Matrix: recommend building B5.9 Series Matrix parser MVP rather than migrating legacy code wholesale.
   - Existing Series Matrix logic is fragmented.
   - Header parsing and row-reader snippets can inform implementation, but there is no complete old parser contract to reuse.
   - MVP should parse header metadata plus the `!series_matrix_table_begin/end` matrix block into current recognition assets and readiness evidence.

3. SOFT longer-term parser: B5.10 SOFT parser MVP remains useful if B5.8B decides not to productize `GEOparse`.
   - If `GEOparse` is accepted as a runtime dependency, B5.8B can become the SOFT carry-over path.
   - If runtime dependency or output semantics are unacceptable, B5.10 should implement a smaller native SOFT parser focused on current recognition needs.

## Next Steps

- B5.8B: prototype a narrow adapter around `app/bioinformatics/legacy/geo_tool/geo_pipeline/process.py` for local full family SOFT only. Do not call legacy CLI output flow directly.
- B5.9: implement an explicit Series Matrix parser MVP in the current recognition architecture.
- Add tests that distinguish container recognition from parsed matrix evidence.
- Add fixtures for `family.soft`, `series_matrix.txt`, `series_matrix.txt.gz`, and diff-result-only tables.
- Keep imported DEG/report-builder semantics unchanged.
- Continue desktop manual testing after parser work because current UI evidence can show a file as recognized while the deeper parser path is still not exercised.

## Verification

- Runtime/business code was not modified.
- No MainLine, Integration, ReleaseBuild, desktop app bundle, or dist files were modified.
- The untracked `docs/bioinformatics/Bioinformatics_handoff_report_20260513.md` was not deleted or changed.
- Full pytest was not run because this stage added only an audit report.
