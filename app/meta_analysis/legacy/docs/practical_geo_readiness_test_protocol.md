# Practical GEO Readiness Test Protocol

This protocol defines how to evaluate the readiness layer on real GEO datasets later. It is documentation only. It does not download data, run DEG, create production downloader behavior, or change `geo_workflow.py`.

## Dataset Classes

Select three classes of GEO datasets for the first practical readiness pass:

- Simple expression matrix with clear groups: a dataset with an obvious matrix-like table and explicit case/control or treatment/control labels.
- Complex probe/platform annotation dataset: a dataset where expression rows are probe ids or platform-specific identifiers and gene mapping requires explicit platform annotation review.
- Messy supplementary or metadata dataset: a dataset with confusing supplementary file names, mixed raw/processed files, incomplete sample annotation, or unclear group labels.

The first pass should use a small number of representative datasets. It should record readiness results and user action needed before any DEG analysis is attempted.

## Per-Dataset Test Steps

For each dataset, record:

1. Download candidate review:
   - list available series matrix, supplementary, raw archive, and platform annotation candidates
   - mark which candidate appears to contain expression data
   - record why other candidates were rejected or deferred
2. Asset readiness:
   - expression matrix status
   - sample annotation status
   - platform annotation status
   - gene annotation status
   - clinical annotation status
3. Gene mapping readiness:
   - detected input id type
   - target id type
   - mapping success rate
   - duplicated targets
   - collapse strategy
   - blocking errors and warnings
4. Sample mapping readiness:
   - matrix sample count
   - metadata sample count
   - matched sample count
   - unmatched matrix samples
   - unmatched metadata samples
   - duplicate sample ids
   - match rate
5. Comparison readiness:
   - selected group column
   - case group
   - control group
   - case count
   - control count
   - missing group samples
   - runnable status
6. Analysis preflight summary:
   - runnable yes/no
   - blocking errors
   - warnings
   - recommended action
7. UI summary:
   - registered preflight result id, if available
   - displayed runnable status
   - displayed blocking error count
   - displayed warning count
   - displayed recommended action

## Recording Template

Use this template for each practical dataset review:

```text
dataset_id:
dataset_class:
files_downloaded:
candidate_files_reviewed:
expression_matrix_detected:
expression_matrix_candidate:
sample_metadata_source:
platform_annotation_source:
gene_identifier_type:
gene_mapping_success_rate:
duplicated_gene_targets:
sample_mapping_rate:
unmatched_matrix_samples:
unmatched_metadata_samples:
comparison_id:
group_column:
case_group:
control_group:
case_count:
control_count:
comparison_runnable:
analysis_preflight_runnable:
blocking_errors:
warnings:
recommended_action:
user_action_needed:
ui_summary_checked:
notes:
```

## Stop Condition

The initial practical GEO pass stops at readiness. It should not:

- run DEG
- schedule tasks
- automatically scan datasets
- call production downloaders
- modify `geo_workflow.py`
- treat warnings as workflow-blocking unless the readiness model marks them as blocking errors

The goal is to identify where real GEO datasets fail before analysis and to harden the readiness layer with explicit, reviewable diagnostics.

## Pre-Protocol Fake Check

Before using any real GEO files, run the fake readiness CLI:

```bash
python3 scripts/run_fake_geo_preflight.py
python3 scripts/run_fake_geo_preflight.py --json
```

This validates the local readiness/preflight chain with in-memory fixtures only. It does not download data, create task results, create artifacts, or run DEG.

The fake CLI is the required safety check before practical GEO readiness testing. It verifies that asset, gene mapping, sample mapping, comparison, and preflight summary construction are functioning in the current checkout without touching real data.

## v0.32 Baseline Entry Criteria

The `v0.32-geo-readiness-preflight-baseline` tag marks the point where fake asset, gene mapping, sample mapping, comparison, and analysis preflight readiness are all available in code, smoke/check output, UI read-only summaries, and developer checks. Practical GEO readiness testing can start after this tag, but it should still stop at readiness review. It should not download through a production downloader, run DEG/enrichment analysis, change `geo_workflow.py`, or treat readiness review as an automated workflow gate.

## Controlled Real GEO Test Design

`docs/controlled_real_geo_readiness_test.md` defines the first controlled real GEO readiness test. The test covers only readiness, mapping, comparison readiness, and preflight. It explicitly excludes DEG, enrichment, survival, TCGA/GTEx, production downloader changes, `geo_workflow.py` changes, scheduler behavior, and automatic task scanning.

The next step requires a human to choose 2-3 real GSE datasets across simple expression matrix, complex probe/platform annotation, and messy supplementary/sample metadata classes.

## Selected PTC Dataset Set

The first controlled readiness set has been manually selected:

- `GSE33630`: simple/main PTC vs normal readiness test for expression matrix, sample metadata, and PTC vs normal comparison readiness.
- `GSE60542`: complex clinical/sample grouping readiness test for primary tumor, nodal metastasis, and N0/N1-style grouping readiness.
- `GSE27155`: multi-class/platform annotation readiness test for PTC subgroup filtering, probe-to-symbol mapping, and platform annotation readiness.

This selection only defines the test scope. It does not download files, run DEG, run enrichment, run survival analysis, change production downloader behavior, or change `geo_workflow.py`.
