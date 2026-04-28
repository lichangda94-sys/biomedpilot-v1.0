# PTC GEO Readiness Test Log Templates

These templates are for controlled readiness documentation only. They do not download data, run DEG, run enrichment, run survival analysis, change production downloader behavior, or change `geo_workflow.py`.

## GSE33630

### Controlled Readiness Dry-Run Checklist

Goal: prepare a controlled readiness inspection for `GSE33630` without downloading data or executing analysis.

Readiness targets:

- expression matrix candidate
- sample metadata source
- PTC vs normal grouping
- sample id match
- gene/platform annotation
- analysis preflight runnable yes/no

Strict exclusions:

- no DEG
- no enrichment
- no survival
- no downloader code change
- no `geo_workflow.py` change

Execution log fields:

```text
commands_attempted:
downloaded_or_inspected_files:
detected_asset_type:
mapping_readiness:
blocking_errors:
warnings:
final_readiness_decision:
tooling_gaps:
```

Current expected command strategy:

```text
1. Record public GEO accession metadata manually.
2. If existing software has a GEO discovery/readiness command, record the exact command and output.
3. If no executable readiness CLI exists for real GEO accessions, record tooling_gap: real_geo_readiness_cli_missing.
4. Do not download files until the controlled inspection task explicitly permits it.
```

```text
dataset_id: GSE33630
reason_for_selection: simple/main PTC vs normal readiness test
expected_test_category: simple expression matrix readiness
expected_groups: PTC vs normal
downloaded_files: none
candidate_expression_matrix: not downloaded; GEO reports processed data in Sample table and a Series Matrix file is available for future controlled inspection
sample_metadata_source: GEO sample table / Series Matrix; supplementary clinical annotation file is available but not downloaded
gene_id_type: Affymetrix GPL570 probe ids expected until Series Matrix or platform annotation is inspected
platform_annotation_status: GPL570 platform identified; probe-to-symbol readiness not evaluated without file inspection
sample_id_match_rate: not evaluated; no expression file downloaded
gene_mapping_success_rate: not evaluated; no expression/platform file downloaded
comparison_readiness: likely candidate PTC vs normal based on public GEO sample labels, but not runnable until files are inspected
runnable: no; blocked at controlled-inspection stage because no real GEO file was downloaded or parsed
blocking_errors:
- expression_matrix_not_downloaded
- real_geo_readiness_cli_missing
warnings:
- public GEO metadata indicates 49 PTC, 45 normal thyroid, and 11 ATC samples; ATC samples must be excluded for the PTC vs normal comparison
- processed data is reported as included within the sample table, so expression extraction may require Series Matrix parsing rather than a simple supplementary matrix file
- clinical annotation exists as a small supplementary file but was not downloaded in this pass
manual_correction_needed:
- confirm whether Series Matrix contains usable processed expression values
- confirm PTC vs normal sample labels and exclude ATC samples
- confirm GPL570 probe-to-symbol mapping strategy
final_decision: not runnable yet; suitable as first controlled readiness benchmark after a real GEO accession inspection CLI or manual file-inspection step is available
```

### Controlled Readiness Inspection Record

Inspection date: 2026-04-26

Commands attempted:

```bash
rg -n "GSE|GEO|geo|readiness|preflight" scripts core analysis extraction local_data -g '!docs/*.md'
rg --files scripts core analysis extraction local_data tests | rg "geo|preflight|readiness|dataset"
python3 scripts/run_fake_geo_preflight.py --json
python3 scripts/run_task_once.py --help
```

Public GEO page inspected:

- `https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=gse33630`

Observed public metadata:

- Status: public.
- Title: normal thyrocytes vs papillary vs anaplastic thyroid carcinomas.
- Organism: Homo sapiens.
- Experiment type: expression profiling by array.
- Platform: GPL570 Affymetrix Human Genome U133 Plus 2.0 Array.
- Samples: 105 total.
- Reported groups: 11 anaplastic thyroid carcinomas, 49 papillary thyroid carcinomas, and 45 normal thyroids.
- GEO download family lists SOFT, MINiML, and Series Matrix files.
- Supplementary files listed by GEO:
  - `GSE33630_RAW.tar`, 849.1 Mb, TAR of CEL files.
  - `GSE33630_clinical-annotation.txt.gz`, 2.8 Kb, TXT.
- GEO reports processed data as included within the Sample table.

Downloaded or inspected files:

- Downloaded files: none.
- Inspected files: public GEO HTML metadata only.

Detected asset type:

- Series Matrix candidate: present in GEO download family, not downloaded.
- Supplementary clinical annotation candidate: present, not downloaded.
- RAW CEL archive: present, not downloaded.
- Processed expression candidate: likely available through Series Matrix or sample table, not parsed.

Mapping readiness:

- Sample metadata: candidate exists via GEO sample table / Series Matrix; not parsed.
- PTC vs normal grouping: likely inferable from sample names ending in `T` and `N`; ATC samples require exclusion.
- Sample id match: not evaluated because no expression matrix was downloaded.
- Gene/platform annotation: GPL570 identified; probe mapping not evaluated.

Blocking errors:

- `expression_matrix_not_downloaded`
- `real_geo_readiness_cli_missing`

Warnings:

- Existing executable readiness CLI is fake-data only and cannot inspect `GSE33630` directly.
- No production downloader changes were made.
- No real GEO files were committed or parsed.

Final readiness decision:

- `GSE33630` remains a suitable simple PTC vs normal readiness benchmark.
- Current software cannot complete a real accession-level readiness inspection without either manual file inspection or a future controlled GEO readiness CLI.
- Analysis preflight runnable status is `no` for this pass because no real expression matrix, metadata table, sample mapping, or gene mapping was parsed.

### Follow-Up After Fake-Backed Accession CLI

Current gap status:

- `real_geo_readiness_cli_missing`: partially mitigated. `scripts/run_geo_accession_readiness.py` now supports `--metadata-file` and can parse saved/fake GEO-like metadata into a candidate inventory.
- `expression_matrix_not_downloaded`: still open. No real Series Matrix, supplementary matrix, or processed expression table has been downloaded or parsed.

Recommended next action:

1. Add live GEO metadata fetch mode to `scripts/run_geo_accession_readiness.py`, or manually save the `GSE33630` GEO metadata page/text and run:

   ```bash
   python3 scripts/run_geo_accession_readiness.py --metadata-file <saved-gse33630-metadata.txt> --gse GSE33630
   python3 scripts/run_geo_accession_readiness.py --metadata-file <saved-gse33630-metadata.txt> --gse GSE33630 --json
   ```

2. Keep the next pass limited to candidate inventory and readiness review.

Still excluded:

- no large file download
- no DEG
- no enrichment
- no survival
- no production downloader change
- no `geo_workflow.py` change

### Saved GEO HTML Metadata CLI Result

Input:

- saved official GEO HTML metadata for `GSE33630`
- saved file size: approximately 47 KB
- no Series Matrix file downloaded
- no RAW archive downloaded
- no supplementary data file downloaded

Command shape:

```bash
python3 scripts/run_geo_accession_readiness.py --metadata-file <temp>/GSE33630_geo_metadata.html --gse GSE33630
python3 scripts/run_geo_accession_readiness.py --metadata-file <temp>/GSE33630_geo_metadata.html --gse GSE33630 --json
```

CLI result:

```text
gse_id: GSE33630
platform_ids: GPL570
series_matrix_candidates: 1
supplementary_candidates: 2
sample_metadata_candidates: 2
expression_candidates: 2
warnings: 0
errors: 0
```

Parser gaps:

- sample_count was not extracted from the saved NCBI GEO HTML.
- title was not extracted from the saved NCBI GEO HTML.
- organism was not extracted from the saved NCBI GEO HTML.
- summary was not extracted from the saved NCBI GEO HTML.

Conclusion:

- Candidate inventory is usable for `GSE33630`.
- Full NCBI GEO HTML metadata field parsing still needs enhancement before accession-level readiness can report complete dataset context.

### Saved Metadata Parser Retest

Input:

- saved official GEO HTML metadata for `GSE33630`
- no Series Matrix, RAW archive, or supplementary data file downloaded

Command:

```bash
python3 scripts/run_geo_accession_readiness.py --metadata-file <temp>/GSE33630_geo_metadata.html --gse GSE33630 --json
```

Retest result:

```text
gse_id: GSE33630
title: Normal thyrocytes vs papillary vs anaplastic thyroid carcinomas
organism: Homo sapiens
summary: non-empty; mentions 11 ATC, 49 PTC, and 45 normal thyroid samples
sample_count: 0
platform_ids: GPL570
series_matrix_candidates: 1
supplementary_candidates: 2
expression_candidates: 2
warnings: sample_count_missing
errors: none
```

Parser retest decision:

- `title`: fixed.
- `organism`: fixed.
- `summary`: fixed enough for readiness context, though summary remains a bounded extracted snippet rather than curated full text.
- `sample_count`: still not fixed for saved NCBI GEO HTML.

Recommendation:

- Improve sample count extraction from GEO HTML sample tables before live metadata fetch.
- Keep `expression_matrix_not_downloaded` open until a controlled Series Matrix download/parse step is explicitly authorized.

### Sample Count Parser Retest

Input:

- temporary saved official GEO HTML metadata for `GSE33630`
- no Series Matrix, RAW archive, or supplementary data file downloaded

Command:

```bash
python3 scripts/run_geo_accession_readiness.py --metadata-file <temp>/GSE33630_geo_metadata.html --gse GSE33630 --json
```

Retest result:

```text
gse_id: GSE33630
title: Normal thyrocytes vs papillary vs anaplastic thyroid carcinomas
organism: Homo sapiens
summary: non-empty; mentions 11 ATC, 49 PTC, and 45 normal thyroid samples
sample_count: 105
platform_ids: GPL570
series_matrix_candidates: 1
supplementary_candidates: 2
expression_candidates: 2
warnings: none
errors: none
```

Parser retest decision:

- `sample_count`: fixed for the saved GSE33630 NCBI GEO HTML layout.
- `title`, `organism`, and `summary`: still extracted.
- Candidate inventory remains usable.

Recommendation:

- Next step can be a live GEO metadata fetch audit/foundation.
- Keep expression matrix download/parse as a separate explicit decision.

### Controlled Live Metadata Fetch Result

Command:

```bash
python3 scripts/run_geo_accession_readiness.py --gse GSE33630 --live --json
```

Result:

```text
live_fetch: failed
failure_type: ssl_error
gse_id: GSE33630
title:
organism:
summary:
sample_count: 0
platform_ids:
series_matrix_candidates: 0
supplementary_candidates: 0
expression_candidates: 0
warnings:
- SSL certificate verify failed
- no_expression_candidate
errors:
- ssl_error
```

Decision:

- Live metadata fetch did not reach parseable GEO metadata in this environment because SSL certificate verification failed.
- The stable `ssl_error` failure path works.
- Continue using `--metadata-file` for GSE33630 until SSL/environment handling is documented or fixed.

Scope note:

- No Series Matrix, RAW archive, supplementary file, or analysis data was downloaded.

### Post-Live Readiness Gap Audit

Live metadata fetch result:

- status: failed
- failure type: `ssl_error`
- metadata parser status: not reached in live mode
- data file download status: none

Interpretation:

- The accession metadata parser is adequate for saved GSE33630 HTML metadata.
- The live fetch helper is present and reports stable errors.
- The local environment cannot currently verify NCBI GEO HTTPS certificates for live fetch.

Recommended next step:

- Add SSL/environment guidance for live metadata fetch, or continue using `--metadata-file` mode for controlled GSE33630 readiness work.

Do not proceed yet to:

- Series Matrix download/parse
- supplementary file download
- DEG / enrichment / survival
- production downloader changes
- `geo_workflow.py` changes

### SSL/Environment Guidance

The current `ssl_error` is a local Python/certificate/network environment failure. It is not treated as an accession-not-found result, and it does not invalidate the saved `GSE33630` metadata parser result.

Safe fallback:

- save the official GEO accession HTML/text with a browser.
- run `scripts/run_geo_accession_readiness.py --metadata-file <saved-gse33630-metadata.html> --gse GSE33630 --json`.
- continue readiness logging from the metadata-file candidate inventory.

Do not disable SSL verification as a default workaround. Do not modify production downloader behavior. Do not proceed to Series Matrix download/parse unless a later scoped task explicitly authorizes it.

Next options:

- A: repair local certificate/Python SSL configuration and retry `--live`.
- B: continue controlled readiness through `--metadata-file`.
- C: add certificate configuration guidance later while keeping verification enabled by default.

### Metadata-File Readiness Path Continuation

The controlled path for `GSE33630` remains `--metadata-file` using saved official GEO accession HTML/text. This path currently extracts:

- `gse_id`: `GSE33630`
- `platform_ids`: `GPL570`
- `title`: normal thyrocytes vs papillary vs anaplastic thyroid carcinomas
- `organism`: Homo sapiens
- `summary`: present
- `sample_count`: 105
- `series_matrix_candidates`: present
- `supplementary_candidates`: present
- `expression_candidates`: present

The `--live` path remains paused by `ssl_error` until the local certificate/Python SSL environment is fixed or documented further.

Next readiness decision:

- decide whether to audit a Series Matrix metadata-only download/parse step as a separate scoped task, or
- continue using manually saved metadata and defer all GEO file downloads.

This continuation still does not download Series Matrix, RAW, supplementary files, or run DEG / enrichment / survival analysis.

### Series Matrix Metadata-Only Audit Plan

Before inspecting any real Series Matrix file, record the intended metadata-only scope:

- target candidate: the `GSE33630` Series Matrix file listed by GEO accession metadata.
- purpose: determine whether the file can provide sample metadata, processed expression candidate signals, and PTC vs normal grouping hints.
- expected platform: GPL570.
- expected samples: 105.
- expected group labels: PTC, normal thyroid, and ATC labels requiring exclusion or explicit grouping rules.

The future parser should be designed first against fake/temp fixtures. It should enforce file-size and line-count limits, avoid RAW/CEL handling, avoid DEG/enrichment/survival execution, and avoid production downloader or `geo_workflow.py` changes.

Current decision:

- Series Matrix metadata-only download/parse is not started in this step.
- The next approved task may be a parser design audit or fake-fixture parser foundation.

### Metadata-Only Readiness Implementation Status

Implemented for controlled `GSE33630` readiness preparation:

- saved GEO HTML metadata parser.
- GSE33630 `sample_count=105` extraction.
- fake-fixture Series Matrix metadata parser.
- sample group detection for PTC, normal, and ATC exclusion candidates.
- metadata-only Series Matrix preflight bridge.

Still not completed:

- real GSE33630 Series Matrix file test.
- expression matrix numeric value parsing.
- GPL570 probe-to-symbol mapping.
- true runnable DEG preflight.

Next manual decision:

- A: manually provide a GSE33630 Series Matrix file for parser testing.
- B: start a Series Matrix expression values parser audit.
- C: start a GPL570 annotation parser audit.
- D: continue with GSE60542 metadata-only readiness testing.

### Real Series Matrix Metadata-Only Retest After Group Fix

Input:

- `tests/geodatabase/GSE33630_series_matrix.txt.gz`
- local manual test file only; not tracked in git.

Readiness result:

- gzip read: yes
- `gse_id`: `GSE33630`
- `platform_ids`: `GPL570`
- `sample_count`: 105
- `sample_metadata_rows`: 105
- PTC count: 49
- normal/control count: 45
- ATC excluded count: 11
- ambiguous count: 0
- comparison candidate: PTC vs normal/control
- comparison readiness: candidate available
- preflight runnable: no
- remaining blocking errors: `asset:expression_matrix_missing`, `expression_matrix_values_not_parsed`
- warnings: gene annotation missing, probe identifier mapping required, ATC excluded from candidate comparison
- parser errors: none

Decision:

- normal/control group detection gap fixed for GSE33630 wording.
- expression matrix numeric values are still not parsed.
- DEG remains blocked and out of scope.

### Metadata-Only Readiness Baseline

Current baseline:

- real GSE33630 Series Matrix metadata parser: passed
- `sample_count`: 105
- PTC: 49
- normal/control: 45
- ATC excluded: 11
- PTC vs normal/control comparison candidate: identifiable

Still not implemented:

- expression matrix numeric values parse
- GPL570 probe-to-symbol mapping
- true runnable DEG preflight
- DEG runner

Next candidates:

- A: Series Matrix expression values parser audit
- B: GPL570 annotation parser audit
- C: GSE60542 metadata-only readiness test

### Series Matrix Expression Parser Design

Design scope:

- find `!series_matrix_table_begin` / `!series_matrix_table_end`.
- parse the first table row as header.
- use the first column as probe/feature id, expected `ID_REF`.
- use remaining columns as GSM matrix sample ids.
- count feature rows and sample columns.
- check numeric values without storing the full matrix.
- count missing and negative values.
- compare matrix sample ids to metadata sample ids.

Report-only output:

- feature count
- matrix sample count
- feature id column
- numeric value status
- missing value count
- negative value count
- sample id match status
- warnings/errors

Boundary:

- no DEG
- no GPL570 annotation parsing
- no full matrix persistence
- no production downloader or `geo_workflow.py` changes

### Real Series Matrix Expression Report Test

Input:

- `tests/geodatabase/GSE33630_series_matrix.txt.gz`
- local manual test file only; not tracked in git.

Read-only expression report result:

- matrix table found: yes
- feature count: 54675
- matrix sample count: 105
- metadata sample count: 105
- feature id column: `ID_REF`
- sample id match status: `match`
- numeric value status: `numeric`
- missing value count: 0
- negative value count: 0
- parser warnings: none
- parser errors: none

Decision:

- `expression_matrix_values_not_parsed` is cleared at the expression-report layer.
- preflight can now consume the expression report.
- DEG remains blocked until GPL570 probe-to-symbol mapping and true runnable DEG preflight are implemented.
- no DEG, enrichment, survival, GPL570 annotation parsing, downloader changes, or `geo_workflow.py` changes were performed.

### Expression Readiness Baseline

Current GSE33630 readiness baseline:

- metadata parser: passed.
- group detection: passed for PTC, normal/control, and ATC exclusion.
- expression matrix report: passed.
- feature count: 54675.
- sample id match status: `match`.
- numeric value status: `numeric`.
- missing value count: 0.
- negative value count: 0.

Remaining blockers:

- GPL570 probe-to-symbol mapping.
- true runnable DEG preflight.
- DEG runner.

Recommended next task: GPL570 annotation parser audit. Do not start DEG, enrichment, survival, production downloader changes, or `geo_workflow.py` changes from this baseline.

## GSE60542

```text
dataset_id: GSE60542
reason_for_selection: complex clinical/sample grouping readiness test
expected_test_category: clinical/sample grouping readiness
expected_groups: primary tumor / nodal metastasis / N0-N1 style groups
downloaded_files:
candidate_expression_matrix:
sample_metadata_source:
gene_id_type:
platform_annotation_status:
sample_id_match_rate:
gene_mapping_success_rate:
comparison_readiness:
runnable:
blocking_errors:
warnings:
manual_correction_needed:
final_decision:
```

## GSE27155

```text
dataset_id: GSE27155
reason_for_selection: multi-class/platform annotation readiness test
expected_test_category: platform annotation and subgroup filtering readiness
expected_groups: PTC subgroup filtering targets to be confirmed manually
downloaded_files:
candidate_expression_matrix:
sample_metadata_source:
gene_id_type:
platform_annotation_status:
sample_id_match_rate:
gene_mapping_success_rate:
comparison_readiness:
runnable:
blocking_errors:
warnings:
manual_correction_needed:
final_decision:
```

### GSE27155 Local SOFT Harness Inspection

Input:

- local untracked file: `tests/geodatabase/GSE27155_family.soft.gz`
- no GEO download performed.
- no Series Matrix file supplied.
- no GPL96 standalone annotation file supplied.

Command:

```bash
python3 scripts/run_real_geo_readiness_test.py \
  --dataset-id GSE27155 \
  --soft-file tests/geodatabase/GSE27155_family.soft.gz \
  --json
```

Observed readiness result:

- gzip SOFT read: yes.
- `gse_id`: `GSE27155`.
- platform ids: `GPL96`.
- sample count: 99.
- sample metadata rows: 99.
- feature count: 22283.
- expression sample count: 99.
- numeric value status: `numeric`.
- missing value count: 0.
- sample id match status: `match`.
- GPL96 probe count: 22283.
- GPL96 mapped probes: 21225.
- GPL96 unmapped probes: 1058.
- GPL96 mapping success rate: 0.9525.
- GPL96 mapping acceptable: true.
- detected groups: `ptc`, `normal`.
- PTC count: 51.
- normal count: 4.
- excluded non-target count: 44.
- ambiguous sample count: 0.
- comparison candidate: PTC vs normal.
- preflight runnable: true.
- harness gap count: 0.

Interpretation:

The local SOFT path is usable for GSE27155 metadata, expression readiness, embedded GPL96 mapping readiness, and group readiness. The first real-file issue was corrected: `morphology of papillary carcinomas: NA` no longer causes follicular/oncocytic/medullary samples to be classified as PTC. Known non-target thyroid tumor classes are excluded from the PTC-vs-normal candidate rather than counted as ambiguous.

Benchmark role:

- GSE27155 is suitable as a multi-class/platform readiness benchmark.
- PTC vs normal/control can be tracked as a readiness comparison candidate.
- normal/control sample count is 4, so reports should show a small-control warning.
- GSE27155 should not be the primary formal DEG demonstration benchmark; GSE33630 remains the better DEG demo candidate.

Remaining work is explicitly scoped for later:

- add and verify small-control warning behavior for the intended comparison.

No formal DEG, enrichment, survival, downloader change, or `geo_workflow.py` change was performed.

## Stop Condition

Each dataset log should stop at readiness and preflight assessment. Do not run DEG, enrichment, survival analysis, scheduler tasks, automatic task scans, production downloads, or `geo_workflow.py` changes from these templates.

### GPL570 Annotation Readiness Manual-Test Plan

Purpose: prepare a future controlled manual test of a locally supplied GPL570 annotation file. This section is a template only; no GPL570 file is downloaded or parsed in this task.

Input template:

```text
platform_id: GPL570
annotation_file_path: <local manual file, not committed>
file_source: <manual browser/GEO platform export/etc>
file_size:
probe_id_column:
gene_symbol_column:
probe_count:
mapped_probe_count:
unmapped_probe_count:
duplicated_symbol_count:
mapping_success_rate:
acceptable:
warnings:
errors:
manual_correction_needed:
final_decision:
```

Expected checks:

- confirm the file is local manual test data and remains untracked.
- identify a probe id column such as `ID` / `ID_REF` / `Probe Set ID`.
- identify a gene symbol column such as `Gene Symbol` / `Symbol`.
- record mapping success rate and duplicate symbol warnings.
- decide whether the mapping report is acceptable for GSE33630 preflight.

Boundaries:

- no GPL570 download in this task.
- no real GPL570 parsing in this task.
- no DEG, enrichment, or survival.
- no production downloader changes.
- no `geo_workflow.py` changes.
```

### GPL570 Annotation Manual File First Parser Check

Input:

- `/Users/changdali/Documents/model9-main-clean/tests/geodatabase/GPL570-55999 (1).txt`
- local manual test file only; not tracked in git.
- file size: 79501274 bytes.

Observed parser result with current fake/local fixture parser:

- platform id: `GPL570`
- probe count: 0
- mapped probe count: 0
- unmapped probe count: 0
- duplicated symbol count: 0
- mapping success rate: 0.0
- acceptable: no
- errors: `probe_id_column_missing`, `gene_symbol_column_missing`

Manual format inspection:

- line 1 starts with comment metadata: `#ID = Affymetrix Probe Set ID`.
- line 11 describes `#Gene Symbol = ...`.
- line 17 contains the actual tabular header beginning with `ID` and including `Gene Symbol`.

Conclusion:

- the current fake/local parser expects the table header on the first line and is not yet compatible with this real GPL570 annotation file layout.
- the next scoped implementation should harden the parser to skip leading comment lines and detect the real header row before parsing.
- no DEG, enrichment, survival, downloader changes, file commits, or `geo_workflow.py` changes were performed.

### GPL570 Annotation Parser Retest After Header Detection Hardening

Input:

- `/Users/changdali/Documents/model9-main-clean/tests/geodatabase/GPL570-55999 (1).txt`
- local manual test file only; not tracked in git.
- file size: 79501274 bytes.

Retest result:

- header row detected: yes.
- probe id column: `ID`.
- gene symbol column: `Gene Symbol`.
- total probes: 54675.
- mapped probes: 45782.
- unmapped probes: 8893.
- duplicated gene symbols: 22902.
- mapping success rate: 0.8373.
- acceptable: yes.
- warnings: `multi_symbol_cells_collapsed_to_first`, `duplicated_symbols_detected`.
- errors: none.
- GPL570 probe-to-symbol mapping blocker: cleared at mapping-report layer.

Scope:

- no GPL570 file was committed.
- no DEG, enrichment, survival, production downloader change, or `geo_workflow.py` change was performed.

### GSE33630 Preflight After GPL570 Mapping

Inputs used read-only from local manual test data:

- `GSE33630_series_matrix.txt.gz`
- `GPL570-55999 (1).txt`

Re-evaluated preflight result:

- `expression_matrix_values_not_parsed`: cleared.
- GPL570 probe-to-symbol mapping: cleared.
- PTC vs normal/control comparison candidate: available.
- PTC samples: 49.
- normal/control samples: 45.
- ATC excluded samples: 11.
- feature count: 54675.
- matrix sample count: 105.
- metadata sample count: 105.
- sample mapping match rate: 1.0.
- mapping success rate: 0.8373.
- preflight runnable: yes.
- remaining blockers: none.
- warnings: multi-symbol cells collapsed to first, duplicated symbols detected, ATC samples excluded, PTC vs normal candidate detected.

Decision:

- GSE33630 now reaches readiness/preflight runnable status for the PTC vs normal/control candidate.
- This does not execute DEG and does not imply DEG runner implementation exists.

### DEG Runner Readiness Decision

Decision for GSE33630 readiness after local manual Series Matrix and GPL570 annotation checks:

- expression values: ok at report/preflight level.
- sample mapping: ok, 105/105 matched.
- group detection: ok, PTC = 49 and normal/control = 45, with ATC = 11 excluded.
- GPL570 mapping: acceptable, mapping success rate = 0.8373.
- readiness/preflight runnable: yes.

Conclusion:

- GSE33630 has reached the conditions for a DEG runner design audit.
- The next step should be `DEG runner design audit`, not direct DEG implementation.

Still not done:

- no DEG runner implementation.
- no limma, DESeq2, or edgeR execution.
- no enrichment or survival.
- no production downloader changes.
- no `geo_workflow.py` changes.

### GSE33630 DEG Runner Design Audit

The first DEG runner design audit is documented in `docs/geo_deg_runner_design.md`. Recommendation: implement a DEG-ready matrix builder before formal DEG statistics.

Reasoning:

- current dependencies do not include scipy/statsmodels.
- GSE33630 readiness is strong enough for matrix preparation.
- formal DEG requires a separate statistical engine decision.

Next implementation candidate: DEG-ready matrix builder with fake fixtures, mean probe-to-symbol collapse reporting, and no formal statistical test.

### GSE33630 DEG-Ready Matrix Manual Test Plan

Current prerequisites already available:

- expression values report: ok.
- sample/group labels: ok, PTC = 49 and normal/control = 45.
- GPL570 mapping: acceptable, mapping success rate = 0.8373.
- readiness/preflight: runnable.

Next real manual test should not run DEG. It should only build or report DEG-ready matrix readiness from local manual files.

Required steps:

- read Series Matrix expression rows from the local `GSE33630_series_matrix.txt.gz` file.
- apply the local GPL570 probe-to-symbol mapping report/table.
- collapse duplicated gene symbols using the declared strategy, initially `mean`.
- output a DEG-ready matrix report.

Record fields:

```text
feature_count:
mapped_feature_count:
gene_count:
sample_count:
case_count:
control_count:
duplicated_gene_count:
collapse_strategy:
ready:
warnings:
errors:
```

Boundary: no formal DEG statistics, no limma/DESeq2/edgeR, no enrichment, no survival, no production downloader changes, and no `geo_workflow.py` changes.

### Controlled DEG-Ready Matrix Manual Test Scope

Input files, kept local and untracked:

- `tests/geodatabase/GSE33630_series_matrix.txt.gz`
- `tests/geodatabase/GPL570-55999 (1).txt`

Manual test target:

- generate DEG-ready matrix readiness report only.
- verify probe-to-symbol mapping application.
- verify duplicated gene symbol collapse readiness with `mean`.
- verify sample grouping remains PTC = 49 and normal/control = 45.

Record fields:

```text
feature_count:
mapped_feature_count:
unmapped_feature_count:
duplicated_gene_count:
gene_count_after_collapse:
case_count:
control_count:
collapse_strategy:
ready:
warnings:
errors:
```

Explicitly not run:

- no formal DEG statistics.
- no p-value.
- no formal logFC.
- no enrichment.
- no DEG result table.

### GSE33630 DEG-Ready Matrix Manual Report

Local untracked inputs:

- `tests/geodatabase/GSE33630_series_matrix.txt.gz`
- `tests/geodatabase/GPL570-55999 (1).txt`

Read-only report result:

- feature count: 54675.
- mapped feature count: 45782.
- unmapped feature count: 8893.
- duplicated gene count: 22902.
- gene count after collapse: 22880.
- sample count: 105.
- case count: 49.
- control count: 45.
- collapse strategy: `mean`.
- ready: yes.
- warnings: `multi_symbol_cells_collapsed_to_first`, `duplicated_symbols_detected`, `duplicated_genes_collapsed`, `unmapped_probes_excluded`.
- errors: none.

Decision: the DEG-ready matrix report is ready enough to enter a minimal two-group DEG statistical runner audit. No p-value, formal logFC, DEG result table, enrichment, production downloader change, or `geo_workflow.py` change was produced.

### GSE33630 Minimal DEG Summary Manual Test Template

Current prerequisites:

- DEG-ready matrix: ready yes.
- case samples: 49 PTC.
- control samples: 45 normal/control.
- gene count after collapse: 22880.

Manual test target:

- compute exploratory mean log2FC summary from a gene-level collapsed matrix.
- do not calculate p-value.
- do not calculate FDR.
- do not classify formal significant DEG hits.

Record fields:

```text
gene_count:
computed_gene_count:
skipped_gene_count:
top_absolute_log2fc_genes:
warnings:
errors:
```

Final label: exploratory DEG summary, not formal DEG result.

### GSE33630 Exploratory Minimal DEG Summary Manual Test

Local untracked inputs:

- `tests/geodatabase/GSE33630_series_matrix.txt.gz`
- `tests/geodatabase/GPL570-55999 (1).txt`

Read-only exploratory summary:

- gene-level collapsed matrix built: yes.
- gene count: 22880.
- computed gene count: 22880.
- skipped gene count: 0.
- case count: 49.
- control count: 45.
- collapse strategy: `mean`.
- pvalue available: false.
- FDR available: false.
- warnings: `multi_symbol_cells_collapsed_to_first`, `duplicated_symbols_detected`, `duplicated_genes_collapsed`, `unmapped_probes_excluded`.
- errors: none.

Top absolute log2FC genes, exploratory only:

| gene_symbol | case_mean | control_mean | log2fc |
| --- | ---: | ---: | ---: |
| RP11-476D10.1 | 7.68858 | 3.39223 | 1.18048 |
| MMRN1 | 3.69983 | 7.94921 | -1.10335 |
| PRR15 | 9.25063 | 4.43057 | 1.06206 |
| ARHGAP36 | 8.56135 | 4.23924 | 1.01403 |
| ZCCHC12 | 11.2367 | 5.66107 | 0.989076 |
| LRP1B | 3.89208 | 7.33184 | -0.913632 |
| RXRG | 8.18636 | 4.45628 | 0.877383 |
| TMEM255A | 6.49285 | 3.6419 | 0.834159 |
| GABRB2 | 8.23099 | 4.64187 | 0.826359 |
| PDZRN4 | 7.13317 | 4.03313 | 0.822642 |

This is an exploratory mean/log2FC summary, not a formal DEG result. No p-value, FDR, formal significance call, enrichment input, production downloader change, or `geo_workflow.py` change was produced.

### GSE33630 Exploratory DEG Summary Baseline

Baseline tag: `v0.38-gse33630-exploratory-deg-summary`.

The GSE33630 exploratory mean/log2FC manual test is recorded as a controlled descriptive baseline:

- gene-level collapsed matrix: built successfully.
- gene count: 22880.
- computed gene count: 22880.
- skipped gene count: 0.
- case count: 49.
- control count: 45.
- collapse strategy: `mean`.
- pvalue available: false.
- FDR available: false.

The formal DEG dependency audit concluded that p-values and FDR should wait for a dedicated scipy/statsmodels dependency decision. This baseline remains exploratory only and is not a formal DEG result.

### GSE33630 Descriptive Volcano Table Design

The next no-dependency descriptive export can use the existing GSE33630 exploratory summary rows to produce `volcano_ready_descriptive_table.csv`.

Required fields are `gene_symbol`, `case_mean`, `control_mean`, `log2fc`, `abs_log2fc`, `status`, `pvalue`, `padj`, `pvalue_available`, `fdr_available`, and `method`.

For this controlled path, `pvalue` and `padj` are empty, `pvalue_available=false`, `fdr_available=false`, and `method=descriptive_mean_log2fc`. The table is exploratory/descriptive only; it must not be interpreted as formal DEG and must not support statistical-significance claims.

### GSE33630 Descriptive Volcano Table Manual Test

The existing exploratory mean/log2FC summary is sufficient to generate a descriptive volcano-ready table shape. The full table was not committed and no plot was generated.

Manual test record:

- descriptive volcano-ready table: generatable.
- total genes: 22880.
- computed genes: 22880.
- skipped genes: 0.
- local artifact path: `<local-temp>/volcano_ready_descriptive_table.csv` (not committed).
- pvalue available: false.
- FDR available: false.
- formal DEG: no.
- significance claim: no.

Top absolute log2FC genes, exploratory only:

| gene_symbol | log2fc |
| --- | ---: |
| RP11-476D10.1 | 1.18048 |
| MMRN1 | -1.10335 |
| PRR15 | 1.06206 |
| ARHGAP36 | 1.01403 |
| ZCCHC12 | 0.989076 |
| LRP1B | -0.913632 |
| RXRG | 0.877383 |
| TMEM255A | 0.834159 |
| GABRB2 | 0.826359 |
| PDZRN4 | 0.822642 |

The table remains a descriptive plotting scaffold only. It contains no p-values, no adjusted p-values, no formal DEG calls, and no enrichment input.

### v0.39 Descriptive Volcano Table Baseline

Baseline tag: `v0.39-descriptive-volcano-table`.

The GSE33630 descriptive volcano table baseline records that the exploratory mean/log2FC summary can produce a plot-shaped CSV table without statistical claims. It records `pvalue_available=false`, `fdr_available=false`, empty `pvalue`/`padj`, and `method=descriptive_mean_log2fc`.

This is not formal DEG and does not include p-values, FDR, limma/DESeq2/edgeR, scipy/statsmodels, enrichment, survival, production downloader changes, or `geo_workflow.py` changes.

### Formal DEG Dependency Decision

Current GSE33630 output remains descriptive only:

- no p-value.
- no FDR.
- no variance model.
- no formal differential expression claim.

Formal DEG would require a two-group test, log2FC, p-value, adjusted p-value, and stable formal result-table semantics.

Dependency decision:

- scipy is recommended if the project allows a first formal two-group statistical test.
- statsmodels is recommended if the project allows FDR correction.
- rpy2/limma, DESeq2, and edgeR are not recommended for the immediate next step.
- if no new dependencies are allowed, continue descriptive-only reporting and UI.

This audit did not install dependencies, change requirements, or run formal DEG.
