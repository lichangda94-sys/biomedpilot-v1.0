# Real Dataset Test Registry

This registry tracks controlled real-dataset readiness tests. It is not a production downloader plan and does not authorize DEG, enrichment, survival, TCGA/GTEx integration, or `geo_workflow.py` changes.

## Purpose

The registry makes real-dataset testing repeatable:

1. select a real dataset with a defined purpose.
2. run a local-file readiness test when inputs are available.
3. generate a structured readiness report.
4. classify gaps.
5. convert real failure modes into small regression fixtures.
6. rerun tests before moving to the next dataset.

## Registry Fields

- `dataset_id`: public accession or local dataset slug.
- `disease_topic`: biological topic under test.
- `data_type`: array, RNA-seq processed matrix, local processed delivery, or other controlled input.
- `platform`: expected platform or identifier type.
- `test_category`: why this dataset is in the test set.
- `expected_groups`: groups expected before analysis.
- `expected_challenges`: known parser, mapping, grouping, or preflight risks.
- `current_status`: not_started, metadata_only, readiness_partial, readiness_passed, blocked, or retired.
- `last_test_result`: short result from the most recent controlled run.
- `blocking_gaps`: normalized gap categories still blocking progress.
- `next_action`: the next scoped task.

## First PTC GEO Dataset Set

| dataset_id | disease_topic | data_type | platform | test_category | expected_groups | expected_challenges | current_status | last_test_result | blocking_gaps | next_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GSE33630 | papillary thyroid carcinoma vs normal/control | GEO expression array | GPL570 | main PTC readiness benchmark | PTC, normal/control, ATC excluded | GEO HTML fields, patient-matched non-tumor wording, GPL570 header after metadata, probe-to-symbol mapping | readiness_passed | metadata, expression report, group detection, GPL570 mapping, DEG-ready matrix, exploratory log2FC, and descriptive volcano table are available | formal_deg_dependency_decision | decide whether to introduce scipy/statsmodels or continue descriptive reporting |
| GSE60542 | PTC clinical/sample grouping | GEO expression array | GPL570 | complex clinical grouping benchmark | primary tumor, nodal metastasis, N0/N1 style groups | clinical group labels, possible paired-like design, comparison confirmation | readiness_passed | PTC-vs-normal readiness usable after excluding 24 LNM/recurrence non-target samples; 34 PTC and 34 normal samples; gap count 0 | none for PTC-vs-normal | decide whether to design separate primary-vs-LNM or N0-vs-N1 comparison |
| GSE27155 | thyroid cancer multi-class/platform annotation | GEO expression array | GPL96 | multi-class and platform annotation benchmark | PTC subgroup candidates, non-PTC groups requiring filtering | multi-class filtering, SOFT metadata parsing, GPL96 annotation, probe-to-symbol mapping, manual comparison confirmation | readiness_passed | local `family.soft.gz` parsed successfully: 99 samples, 22283 features, GPL96 mapping success rate 0.9525, 51 PTC, 4 normal, 44 excluded non-target, 0 ambiguous, gap count 0 | comparison_policy_needs_confirmation | decide whether PTC vs 4 normal controls is acceptable for next-stage analysis readiness |

## Current Test Policy

- Full real GEO/GPL files remain local and untracked.
- Only small fixtures that isolate a failure mode should be committed.
- Generated `real_dataset_tests/` reports are local by default and ignored by git.
- Report summaries may be copied into docs only when they contain no large data and no sensitive/private data.
- Readiness tests stop before formal DEG unless a separate scoped task explicitly allows it.

## Structured Report And Gap Taxonomy

The real dataset harness uses `RealDatasetReadinessReport` to normalize outputs from metadata parsing, Series Matrix parsing, group detection, expression reporting, platform mapping, and preflight.

Gap categories are:

- `download_gap`
- `metadata_parse_gap`
- `series_matrix_parse_gap`
- `expression_matrix_gap`
- `sample_mapping_gap`
- `gene_mapping_gap`
- `group_detection_gap`
- `comparison_readiness_gap`
- `preflight_gap`
- `ui_display_gap`
- `manual_confirmation_required`

Each gap should be specific enough to become either a parser/readiness fix or a small regression fixture.

## Local-File Real GEO Readiness Test Runner

`scripts/run_real_geo_readiness_test.py` is the controlled local-file harness for real GEO readiness tests. It is not a production downloader and does not access the network.

Supported inputs:

```bash
python3 scripts/run_real_geo_readiness_test.py \
  --dataset-id GSE33630 \
  --metadata-file <saved_geo_metadata.html> \
  --series-matrix-file <series_matrix.txt.gz> \
  --platform-annotation-file <GPL570.txt> \
  --json
```

Optional report output:

```bash
python3 scripts/run_real_geo_readiness_test.py \
  --dataset-id GSE33630 \
  --metadata-file <saved_geo_metadata.html> \
  --series-matrix-file <series_matrix.txt.gz> \
  --platform-annotation-file <GPL570.txt> \
  --output-dir real_dataset_tests/GSE33630
```

The runner connects existing readiness components:

- GEO accession metadata parser.
- Series Matrix metadata parser.
- Series Matrix expression report.
- GEO sample group detection.
- platform annotation mapping report.
- analysis preflight summary.
- real dataset gap classifier.

It does not download GEO files, run DEG, run enrichment, run survival, create `TaskResultRecord`, create execution logs, or modify `geo_workflow.py`.

The command is included in local environment readiness, packaging readiness, and developer quick checks through its `--help` path only. Dev checks do not run a real dataset, do not read local manual data, and do not create reports.

## Fixture Regression Policy

The fixture policy is documented in `docs/real_dataset_fixture_policy.md`. Every parser/readiness gap found through real data should become a small regression fixture when it is safe to do so. The fixture should reproduce the specific failure mode without committing the full source file.

Gap-to-fixture expectations:

- `metadata_parse_gap`: reduce to a saved GEO HTML/text snippet.
- `series_matrix_parse_gap`: reduce to Series Matrix metadata or matrix-table lines.
- `group_detection_gap`: reduce to sample title/source/characteristics lines.
- `platform_mapping_gap`: reduce to platform annotation header and representative rows.
- `sample_mapping_gap`: reduce to matrix sample ids plus metadata sample ids.
- `comparison_readiness_gap`: reduce to sample metadata and expected comparison rule.

Committed fixtures should use `tests/fixtures/geo/<dataset>_<gap_type>_<short_desc>.txt`, remain small, avoid full GEO/GPL files, and be covered by a unit test. Full real files and generated reports remain local-only.

## v0.40 Real Dataset Harness Baseline

The v0.40 baseline records the Real Dataset Test Harness MVP:

- `RealDatasetReadinessReport` normalizes dataset-level readiness outputs.
- `RealDatasetGap` classifies readiness failures into stable categories for follow-up.
- `scripts/run_real_geo_readiness_test.py` runs a controlled local-file harness from manually supplied metadata, Series Matrix, and platform annotation files.

The GSE33630 harness smoke result is the first benchmark record:

- recommended action: `ready_for_manual_review`.
- gap count: 0.
- preflight runnable: true.
- feature count: 54675.
- sample count: 105.
- mapping success rate: 0.8373.
- detected groups: `['ptc', 'normal']`.
- excluded ATC samples: 11.

Boundaries remain unchanged: no formal DEG, enrichment, survival, production downloader, automatic real dataset download, `TaskResultRecord`, execution log, or `geo_workflow.py` changes.

Next work should display readiness reports in the UI and test GSE60542/GSE27155 through the same local-file harness when their files are provided.

## Next Real Dataset Decision Brief

Three controlled paths are available after the GSE33630 harness smoke:

### Option A: GSE60542

- purpose: primary tumor / nodal metastasis / N0-N1 style grouping benchmark.
- expected benefit: stresses complex clinical/sample metadata, metastasis wording, nodal status grouping, and comparison-readiness warnings.
- required local files: saved GEO metadata HTML/text, Series Matrix file, and any local platform annotation file needed for mapping.
- risk: grouping may require manual confirmation because primary/metastasis and N0/N1 are not a simple two-group PTC vs normal comparison.

### Option B: GSE27155

- purpose: multi-pathology and platform-annotation benchmark.
- expected benefit: stresses multi-class filtering, PTC subgroup selection, ambiguous disease labels, and platform mapping behavior.
- required local files: saved GEO metadata HTML/text, Series Matrix file, and the relevant platform annotation file.
- risk: multi-class cohorts may be blocked by comparison readiness until a specific target comparison is manually selected.

### Option C: Continue GSE33630

- purpose: deepen the existing benchmark.
- expected benefit: uses a known-ready dataset for either formal DEG dependency decision or descriptive demo polish.
- required local files: current local GSE33630 Series Matrix and GPL570 annotation files remain sufficient for descriptive paths.
- risk: formal DEG requires a separate scipy/statsmodels dependency decision; without that, work should stay descriptive.

Recommended next step: run GSE60542 through the local-file harness after the user provides local files. It is the best next coverage increase because it tests complex sample metadata and grouping rather than repeating the already-ready GSE33630 path.

## GSE60542 First Harness Result

Local files were provided for GSE60542 and the first controlled local-file harness inspection completed without downloading data:

- Series Matrix file: local untracked `GSE60542_series_matrix.txt.gz`.
- platform annotation file: local untracked GPL570 annotation.
- family SOFT file: local untracked `GSE60542_family.soft.gz`, not consumed by the harness because compressed SOFT metadata is not currently a metadata-file input.

Initial observed result:

- expression matrix report: usable, numeric, 54675 features, 92 samples, zero missing values, sample ids matched.
- platform mapping: acceptable, mapping success rate 0.8373.
- group detection: `normal` and `ptc` detected.
- comparison candidate: PTC vs normal, runnable with 36 case samples and 34 controls.
- preflight: runnable.
- gap count: 1.
- gap category: `group_detection_gap`.
- gap code: `ambiguous_samples`.
- ambiguous samples: 22, mainly lymph node metastasis/recurrence/N1-related labels.

Current status should be treated as `needs_grouping_decision`, not parser failure. The next action is manual comparison-scope selection: exclude LNM/recurrence for PTC-vs-normal, define primary-vs-LNM, or define N0-vs-N1.

The first follow-up selected the PTC-vs-normal exclusion policy. LNM/recurrence samples are now classified as `excluded_non_target` for this candidate comparison, based only on sample label fields.

Retest result:

- gap count: 0.
- ambiguous samples: 0.
- excluded non-target samples: 24.
- PTC samples in comparison: 34.
- normal samples in comparison: 34.
- preflight runnable: true.
- recommended action: `ready_for_manual_review`.

GSE60542 is now passed for the PTC-vs-normal readiness path. Primary-vs-LNM and N0-vs-N1 remain separate future comparison designs.

## GSE60542 PTC-vs-Normal Baseline

Current GSE60542 status for the selected comparison:

- status: `readiness_passed`.
- selected comparison: PTC vs normal.
- PTC samples: 34.
- normal samples: 34.
- excluded non-target samples: 24.
- gap count: 0.
- preflight runnable: true.
- recommended action: `ready_for_manual_review`.

This completes GSE60542 for the PTC-vs-normal readiness path. It does not complete primary-vs-LNM or N0-vs-N1 comparison designs.
