# Controlled Real GEO Readiness Test Design

This design defines the first controlled real GEO readiness test. It is documentation only. It does not download GEO data, run DEG, run enrichment, run survival analysis, touch TCGA/GTEx, change production downloader behavior, change `geo_workflow.py`, start a scheduler, or scan tasks automatically.

## First-Round Goal

The first controlled test should evaluate only:

- readiness
- gene/probe/sample mapping
- comparison readiness
- analysis preflight summary
- UI/read-only readiness presentation, if a preflight result is registered manually

It should not evaluate:

- DEG runner behavior
- enrichment
- survival analysis
- TCGA/GTEx workflows
- scheduler behavior
- automatic task scans

## GSE Selection Classes

Select 2-3 real GSE datasets after human review. The set should cover these classes:

1. Simple expression matrix:
   - processed matrix is obvious.
   - sample groups are clear.
   - gene identifiers are already usable or easy to map.

2. Complex probe/platform annotation:
   - expression rows are probe ids or platform-specific ids.
   - platform annotation is required for symbol/Ensembl mapping.
   - duplicate target mappings may appear.

3. Messy supplementary or sample metadata:
   - supplementary files have unclear names or mixed raw/processed content.
   - sample metadata is incomplete or inconsistent.
   - group labels require manual confirmation.

## Per-Dataset Record

Record these fields for every selected dataset:

```text
GSE id:
disease/topic:
expected groups:
downloaded files:
candidate expression matrix:
sample metadata source:
gene id type:
sample id match rate:
gene mapping success rate:
comparison readiness:
runnable yes/no:
blocking errors:
warnings:
recommended user action:
```

## Failure Classification

Use these failure categories:

- download failure
- no expression matrix
- sample metadata missing
- sample mismatch
- gene mapping insufficient
- comparison not runnable
- file classification uncertain
- user confirmation required

Multiple categories may apply to the same dataset. Warnings should remain non-blocking unless the readiness model marks the condition as a blocking error.

## Boundary

The controlled test must preserve these boundaries:

- no DEG
- no enrichment
- no survival
- no TCGA/GTEx
- no production downloader change
- no `geo_workflow.py` change
- no scheduler
- no automatic task scan
- no workflow-blocking behavior from warnings alone

## Manual Selection Requirement

Before any controlled real GEO readiness test begins, a human must choose 2-3 real GSE datasets and record why each dataset was selected. Codex should stop here until those GSE ids are provided.

## Selected PTC Readiness Test Datasets

The first manually selected PTC GEO readiness datasets are:

1. `GSE33630`
   - Type: simple/main PTC vs normal readiness test.
   - Goal: expression matrix readiness, sample metadata readiness, and PTC vs normal comparison readiness.

2. `GSE60542`
   - Type: complex clinical/sample grouping readiness test.
   - Goal: primary tumor, nodal metastasis, and N0/N1-style grouping readiness.

3. `GSE27155`
   - Type: multi-class/platform annotation readiness test.
   - Goal: PTC subgroup filtering, probe-to-symbol mapping, and platform annotation readiness.

This selection does not authorize downloads or analysis execution by itself. The next step is to create per-dataset test logs, then perform controlled readiness review only when explicitly requested.

## Selected Dataset Boundary

For the selected PTC datasets, the first pass remains limited to:

- readiness
- mapping
- preflight

It still excludes DEG, enrichment, survival, TCGA/GTEx, production downloader changes, `geo_workflow.py` changes, scheduler behavior, and automatic task scanning.

## Test Log Templates

Per-dataset templates for `GSE33630`, `GSE60542`, and `GSE27155` are recorded in `docs/ptc_geo_readiness_test_log.md`. The templates capture:

- dataset id
- reason for selection
- expected test category
- expected groups
- downloaded files
- candidate expression matrix
- sample metadata source
- gene id type
- platform annotation status
- sample id match rate
- gene mapping success rate
- comparison readiness
- runnable status
- blocking errors
- warnings
- manual correction needed
- final decision

The templates are blank records for future manual testing. They do not authorize data download or analysis execution.

## GSE33630 Dry-Run Checklist

`GSE33630` is the first selected dataset for controlled readiness inspection. The dry-run checklist is recorded in `docs/ptc_geo_readiness_test_log.md` and covers expression matrix candidate review, sample metadata source, PTC vs normal grouping, sample id matching, gene/platform annotation, and analysis preflight runnable status.

The checklist also records commands attempted, downloaded or inspected files, detected asset type, mapping readiness, blocking errors, warnings, final readiness decision, and tooling gaps. If no existing executable readiness CLI can inspect a real GEO accession without custom downloader work, record `real_geo_readiness_cli_missing` as a gap rather than implementing new functionality inside the test.

## GSE33630 Controlled Inspection Result

The first controlled inspection for `GSE33630` was limited to existing tooling and public GEO metadata. No GEO files were downloaded, no downloader code was changed, and no analysis was executed.

Public GEO metadata indicates that `GSE33630` is an expression profiling by array dataset on GPL570 with 105 samples: 49 papillary thyroid carcinoma, 45 normal thyroid, and 11 anaplastic thyroid carcinoma samples. GEO exposes Series Matrix files, a large RAW CEL archive, and a small clinical annotation supplementary file. Processed data is reported as included within the sample table.

Current software has a fake-data GEO preflight CLI, dataset readiness helpers, mapping readiness helpers, comparison readiness helpers, and analysis preflight summary support. It does not yet have an executable real GEO accession readiness CLI that can inspect `GSE33630` without manual file handling. The inspection therefore records `real_geo_readiness_cli_missing` and `expression_matrix_not_downloaded` as blocking readiness issues for this pass.

`GSE33630` remains suitable as the simple PTC vs normal benchmark, but it is not preflight-runnable in this controlled pass because no expression matrix, sample metadata table, sample mapping, or probe-to-symbol mapping was parsed.

## GSE33630 Follow-Up After Fake-Backed CLI

The `real_geo_readiness_cli_missing` gap is now partially mitigated by `scripts/run_geo_accession_readiness.py`. The command can parse a local saved/fake GEO-like metadata file with `--metadata-file` and output candidate inventory counts for Series Matrix, supplementary files, sample metadata, and expression candidates.

The remaining blocking gap for `GSE33630` is `expression_matrix_not_downloaded`. No real Series Matrix or supplementary expression file has been downloaded, parsed, or mapped into `DatasetAssetReadinessReport` / `AnalysisPreflightSummary` inputs.

Next options:

- add live GEO metadata fetch mode to the accession readiness CLI; or
- manually save the `GSE33630` metadata page/text and run the current `--metadata-file` mode.

Both options must remain readiness-only. They must not download large raw archives, run DEG, change production downloader code, or modify `geo_workflow.py`.

## GSE33630 Saved Metadata CLI Result

The `--metadata-file` mode was tested with a saved official GEO HTML metadata file for `GSE33630`. The file was approximately 47 KB. No Series Matrix, RAW archive, or supplementary data file was downloaded.

The CLI successfully reported:

- `gse_id`: `GSE33630`
- `platform_ids`: `GPL570`
- `series_matrix_candidates`: 1
- `supplementary_candidates`: 2
- `sample_metadata_candidates`: 2
- `expression_candidates`: 2
- `warnings`: 0
- `errors`: 0

Remaining parser gaps:

- `sample_count` was not extracted.
- `title` was not extracted.
- `organism` was not extracted.
- `summary` was not extracted.

Conclusion: candidate inventory is usable, but full GEO HTML metadata parsing still needs enhancement before the CLI can fully replace manual accession metadata review.

## GSE33630 Parser Retest

After improving GEO HTML/text field parsing, the saved official GEO HTML metadata for `GSE33630` was tested again through `scripts/run_geo_accession_readiness.py --metadata-file`.

Retest outcome:

- `gse_id`: `GSE33630`
- `title`: extracted
- `organism`: extracted as `Homo sapiens`
- `summary`: extracted and non-empty
- `sample_count`: still not extracted from the saved NCBI GEO HTML
- `platform_ids`: `GPL570`
- `series_matrix_candidates`: 1
- `supplementary_candidates`: 2
- `expression_candidates`: 2
- `warnings`: `sample_count_missing`
- `errors`: none

The parser gap is now narrowed to sample-count extraction from the actual NCBI GEO HTML shape. Candidate inventory remains usable, and no data files were downloaded.

## GSE33630 Sample Count Parser Retest

After adding support for the NCBI GEO `Samples (N)` table-label pattern, the saved official GEO HTML metadata for `GSE33630` was tested again.

Retest outcome:

- `gse_id`: `GSE33630`
- `title`: extracted
- `organism`: `Homo sapiens`
- `summary`: extracted and non-empty
- `sample_count`: 105
- `platform_ids`: `GPL570`
- `series_matrix_candidates`: 1
- `supplementary_candidates`: 2
- `expression_candidates`: 2
- `warnings`: none
- `errors`: none

The parser gap for saved GSE33630 metadata is fixed. The remaining readiness gap is not metadata parsing; it is the still-explicitly-deferred expression matrix download/parse step.

## Live GEO Metadata Fetch Audit

The next controlled step may add `--live` support to `scripts/run_geo_accession_readiness.py`. This should fetch only the public NCBI GEO accession metadata page and reuse `parse_geo_accession_metadata(text)` to build `GeoAccessionInventory`.

Proposed CLI parameters:

- `--gse GSE33630`
- `--live`
- `--json`
- `--timeout <seconds>`

Allowed fetch target:

- the GEO accession metadata page for the provided GSE id

Explicitly excluded:

- Series Matrix download
- RAW archive download
- supplementary expression file download
- FASTQ/SRA access
- DEG, enrichment, or survival analysis
- production downloader changes
- `geo_workflow.py` changes

Failure categories should be stable:

- `network_unavailable`
- `ssl_error`
- `accession_not_found`
- `fetch_timeout`
- `metadata_parse_failed`

The live metadata fetch should remain a readiness helper, not a production downloader. It should be opt-in via `--live`, covered by mocked-network tests, and safe to fail without changing workflow state.

## GSE33630 Controlled Live Metadata Fetch Result

Command:

```bash
python3 scripts/run_geo_accession_readiness.py --gse GSE33630 --live --json
```

Observed result:

- live fetch succeeded: no
- failure type: `ssl_error`
- `gse_id`: `GSE33630`
- `title`: not available because metadata fetch failed
- `organism`: not available because metadata fetch failed
- `summary`: not available because metadata fetch failed
- `sample_count`: 0
- `platform_ids`: none
- `series_matrix_candidates`: 0
- `supplementary_candidates`: 0
- `expression_candidates`: 0
- `warnings`: SSL certificate verification failure, `no_expression_candidate`
- `errors`: `ssl_error`

No GEO data files were downloaded. The failure confirms that the live fetch path reports a stable SSL/environment error rather than falling through to downloader behavior.

## Post-Live GSE33630 Readiness Gap Analysis

The live accession metadata path is now implemented as a narrow readiness helper, but the first controlled `GSE33630` live check did not reach parser execution because the local environment failed HTTPS certificate verification. This is an environment/SSL readiness gap, not a GEO parser regression and not an expression matrix parsing result.

Current status:

- `--metadata-file` mode remains the reliable controlled path for saved `GSE33630` metadata.
- `--live` mode is present and returns stable `ssl_error` output in this environment.
- no Series Matrix, RAW archive, supplementary expression file, FASTQ/SRA, or analysis data was downloaded.
- no preflight result, task result, artifact, or execution log was created.

Recommended next step:

- Add SSL/environment guidance for live accession metadata fetch, or continue the controlled `GSE33630` readiness pass with manually saved metadata via `--metadata-file`.

Do not proceed yet to Series Matrix download/parse. That should be a separate explicit audit after live metadata access is reliable or after a metadata-file based candidate review confirms the smallest safe file to inspect.

## GSE33630 SSL Guidance

The `ssl_error` observed during `GSE33630 --live` is treated as a local environment issue: the Python runtime could not verify the HTTPS certificate chain for the GEO metadata page. It is not evidence that `GSE33630` is unavailable, and it is not a parser failure.

Controlled fallback path:

- use a browser to save the official GEO accession HTML/text.
- run `scripts/run_geo_accession_readiness.py` with `--metadata-file`.
- keep recording candidate inventory only until a later task explicitly authorizes a narrower file download/parse audit.

Do not work around this by disabling SSL verification. The production downloader remains unchanged, and the controlled readiness test should continue to avoid Series Matrix, RAW, supplementary, FASTQ/SRA, DEG, enrichment, and survival execution.

Next options:

- A: fix local certificate/Python SSL configuration, then retry `--live`.
- B: continue with saved metadata through `--metadata-file`.
- C: document configurable certificate handling later, without introducing an insecure default.

## GSE33630 Metadata-File Readiness Continuation

The controlled readiness path now continues through saved metadata rather than live fetching. The saved official GEO accession HTML/text path extracts the accession id, GPL570 platform id, title, organism, non-empty summary, `sample_count=105`, Series Matrix candidates, supplementary candidates, and expression candidates.

Live fetch remains paused because of `ssl_error`. This is an environment issue, not a parser failure and not an accession-not-found result.

Next readiness decision:

- audit whether a small Series Matrix metadata-only download/parse step should be scoped next; or
- continue with manually saved metadata and defer all GEO file download/parse work.

No download or analysis is authorized by this continuation. Series Matrix, RAW, supplementary files, DEG, enrichment, survival, production downloader changes, and `geo_workflow.py` changes remain out of scope.

## GSE33630 Series Matrix Metadata-Only Audit Design

The next controlled step should be a separate Series Matrix metadata-only audit before any implementation or file download. The goal is to decide whether a small Series Matrix file can be safely inspected later to bridge accession-level candidate inventory into sample metadata, expression candidate detection, and comparison readiness.

Proposed audit questions:

- Which Series Matrix candidate is the smallest safe inspection target?
- Does the candidate likely contain processed expression values, phenotype metadata, or both?
- Which rows/headers would identify sample ids, platform ids, sample titles, source names, and characteristics?
- Can PTC, normal, and ATC labels be detected without running DEG?
- Are probe ids expected, and is GPL570 annotation needed before gene mapping readiness can be scored?
- What maximum file-size and line-count guard should a later parser enforce?

Required boundaries:

- no download in the audit task itself.
- no RAW/CEL archive handling.
- no supplementary expression file download.
- no DEG, enrichment, survival, or Module 5 execution.
- no production downloader or `geo_workflow.py` changes.
- no task result, artifact, or execution log creation.

Recommended next scoped implementation, if approved later:

- add a metadata-only Series Matrix parser using fake/temp fixtures first.
- keep any real file inspection manual and explicit.
- record sample metadata candidates, expression matrix availability, group label hints, and blocking errors.

## Series Matrix Metadata Parser Foundation

The fake-fixture Series Matrix metadata parser foundation is now scoped as metadata-only. It can read local text, `.txt`, or `.txt.gz` fixture input and extract Series accession, platform ids, sample ids, sample count, titles, source names, and characteristics into `SeriesMatrixMetadataReport`.

The parser does not parse numeric expression matrix values and does not inspect the real GSE33630 Series Matrix file. Any real GSE33630 file test remains a separate manual decision after this metadata-only foundation.

## GSE33630 Group Detection Foundation

The metadata-only group detection helper can consume Series Matrix sample metadata rows and identify candidate `ptc` and `normal` groups while marking ATC samples as excluded candidates. It does not create a final comparison and does not decide that DEG is runnable.

For GSE33630, this means PTC vs normal labels can be surfaced as readiness candidates from fake/minimal Series Matrix metadata fixtures, while ATC samples remain explicit exclusions requiring user review.

After the first real-file metadata-only test, normal/control detection was extended to cover GSE33630 wording such as `patient-matched non-tumor control` and related non-tumor/adjacent-normal synonyms.

## GSE33630 Metadata-Only Preflight Bridge

The metadata-only bridge can now combine fake-fixture Series Matrix metadata and group detection into `AnalysisPreflightSummary`. It records PTC vs normal as a candidate readiness signal and preserves ATC as an excluded warning, but it still blocks execution with `expression_matrix_values_not_parsed`.

This is the correct behavior before any real GSE33630 Series Matrix file is manually provided and before any expression matrix numeric values are parsed.

## GSE33630 Metadata-Only Readiness Implementation Status

Completed foundations:

- saved GEO HTML metadata parser.
- sample count extraction for saved GSE33630 metadata.
- fake-fixture Series Matrix metadata parser.
- group detection for PTC, normal thyroid, and excluded ATC candidates.
- metadata-only preflight bridge to `AnalysisPreflightSummary`.

Remaining gaps:

- no real GSE33630 Series Matrix file has been tested.
- no expression matrix numeric values are parsed.
- no GPL570 probe-to-symbol mapping is implemented.
- no true runnable DEG preflight exists.

Next manual decision is required before continuing:

- A: provide a GSE33630 Series Matrix file manually for parser testing.
- B: audit Series Matrix expression value parsing.
- C: audit GPL570 annotation parsing.
- D: continue with GSE60542 metadata-only readiness testing.

## GSE33630 Real Series Matrix Metadata-Only Retest

A local manual `GSE33630_series_matrix.txt.gz` file was used for a read-only metadata-only parser test. The file remains untracked and is not part of the repository.

Observed result:

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

The normal/control group detection gap is fixed for the GSE33630 wording `patient-matched non-tumor control`. The remaining blocker is expression matrix numeric value parsing, plus later GPL570 probe-to-symbol mapping before any true DEG preflight can be runnable.

## GSE33630 Metadata-Only Readiness Baseline

The current controlled baseline confirms:

- real GSE33630 Series Matrix metadata parser passed on a manually supplied local file.
- `sample_count=105`.
- PTC samples: 49.
- normal/control samples: 45.
- ATC excluded samples: 11.
- PTC vs normal/control comparison candidate is identifiable from metadata.

Still not implemented:

- expression matrix numeric values parse.
- GPL570 probe-to-symbol mapping.
- true runnable DEG preflight.
- DEG runner.

Next candidates are Series Matrix expression value parser audit, GPL570 annotation parser audit, or GSE60542 metadata-only readiness testing.

## Series Matrix Expression Parser Design

The expression parser should be a report-only layer over an already available Series Matrix fixture. It should identify the table bounded by `!series_matrix_table_begin` and `!series_matrix_table_end`, parse the header, treat the first column as the probe/feature id column, and treat the remaining columns as GSM sample ids.

For GSE33630 readiness, the first parser should report feature count, matrix sample count, feature id column, matrix sample ids, numeric value status, missing value count, negative value count, and matrix-vs-metadata sample id match status. It should not retain or write the complete expression matrix.

This parser does not run DEG, does not perform GPL570 annotation, and does not determine that the dataset is ready for DEG by itself.

## GSE33630 Expression Matrix Report Test

A manually supplied local `GSE33630_series_matrix.txt.gz` file was used for a read-only expression report test. The file remains untracked and is not part of the repository.

Observed result:

- matrix table found: yes
- feature count: 54675
- matrix sample count: 105
- metadata sample count: 105
- feature id column: `ID_REF`
- sample id match status: `match`
- numeric value status: `numeric`
- missing value count: 0
- negative value count: 0
- warnings: none
- errors: none

The expression report clears the previous expression-table parsing gap at the report layer. Remaining blockers are GPL570 probe-to-symbol mapping and true runnable DEG preflight integration. No DEG, enrichment, survival, production downloader changes, or `geo_workflow.py` changes were performed.

## GSE33630 Expression Readiness Baseline

The current controlled GSE33630 readiness status is:

- saved GEO accession metadata parser: passed.
- real Series Matrix metadata parser: passed.
- group detection: passed with 49 PTC, 45 normal/control, and 11 ATC excluded.
- expression matrix report: passed with 54675 features and 105 matrix samples.
- sample id match status: `match`.
- numeric value status: `numeric`.
- missing value count: 0.
- negative value count: 0.

Remaining blockers:

- GPL570 probe-to-symbol mapping.
- true runnable DEG preflight.
- DEG runner.

Recommended next step is a GPL570 annotation parser audit. Do not proceed to DEG, enrichment, survival, production downloader changes, or `geo_workflow.py` changes from this baseline.

## GSE33630 Readiness Gap Analysis

`GSE33630` is still a good first simple PTC vs normal readiness benchmark. Public GEO metadata exposes the expected PTC and normal sample groups, a known array platform, Series Matrix files, a RAW CEL archive, and a small clinical annotation file. The dataset is therefore appropriate for testing the path from GEO accession review to expression/metadata/gene mapping readiness.

Current behavior that worked:

- Public GEO metadata review identified dataset topic, platform, sample count, and high-level groups.
- File classification at the metadata level distinguished Series Matrix, RAW CEL archive, and clinical annotation candidates.
- Existing fake preflight tooling verified that the readiness chain can aggregate asset, gene mapping, sample mapping, comparison, and final preflight summaries when structured inputs are available.
- The test log captured blocking errors and warnings without changing downloader code or running analysis.

Gaps exposed:

- Downloader gap: there is no controlled real GEO accession readiness command that can inspect a GSE id and list candidate Series Matrix / supplementary assets without changing production downloader code.
- Asset classification gap: current real-GEO classification is manual; the software does not yet classify `GSE33630` files into expression matrix, sample metadata, raw archive, and annotation roles from accession-level metadata.
- Sample mapping gap: no parsed expression matrix or metadata table means GSM/sample id matching cannot be evaluated.
- Gene mapping gap: GPL570 is identified, but probe-to-symbol readiness cannot be scored without inspecting platform annotation or expression feature ids.
- Group detection gap: PTC vs normal appears likely, but ATC exclusion and group labels are not machine-validated.
- CLI/tooling gap: the available `scripts/run_fake_geo_preflight.py` is intentionally fake-data only; there is no `run_geo_readiness_once.py`-style command for real accession readiness.
- UI readiness display gap: UI can display registered preflight summaries, but there is no real-GEO accession preflight result to display for `GSE33630` yet.

Recommended next task:

- Add a controlled, read-only real GEO readiness CLI audit or foundation that accepts a GSE id, records public metadata and candidate asset links, and stops before downloading large files or running analysis.

Alternative:

- Continue to `GSE60542` only if the goal is to compare metadata complexity manually before adding real-GEO accession tooling.

## Real GEO Accession Readiness CLI Design

Recommended command name:

```bash
python3 scripts/run_geo_accession_readiness.py --gse GSE33630
python3 scripts/run_geo_accession_readiness.py --gse GSE33630 --json
```

Inputs:

- `--gse`: required accession id for live/public metadata mode, for example `GSE33630`.
- `--json`: optional stable machine-readable output.
- Future safe extension: `--metadata-file <path>` for manually saved GEO metadata, so tests can run without network access.

First-stage responsibilities:

- fetch or read public GEO accession metadata
- inventory Series Matrix candidates
- inventory supplementary file candidates
- identify platform/GPL candidates
- identify sample metadata candidates
- identify likely expression candidates from Series Matrix, sample table, or supplementary metadata
- output a candidate inventory with warnings and errors

First-stage exclusions:

- no large file download
- no RAW archive download
- no DEG
- no enrichment
- no survival
- no production downloader change
- no `geo_workflow.py` change
- no task/result/log creation

Stable failure codes:

- `network_unavailable`
- `accession_not_found`
- `metadata_parse_failed`
- `no_expression_candidate`

Future integration:

- Convert candidate inventory into `DatasetAssetReadinessReport` inputs.
- Feed parsed platform/sample/expression candidates into `AnalysisPreflightSummary` only after a controlled file-inspection step exists.
- Keep warnings reporting-only until a user explicitly runs a readiness or preflight command.

## Fake-Backed GEO Accession Readiness CLI

The first implementation stage should support a local metadata-file mode before live metadata fetch:

```bash
python3 scripts/run_geo_accession_readiness.py --metadata-file <path>
python3 scripts/run_geo_accession_readiness.py --metadata-file <path> --json
```

This mode parses a saved or fake GEO-like metadata text file and reports accession id, sample count, platform ids, Series Matrix candidate count, supplementary candidate count, sample metadata candidate count, expression candidate count, warnings, and errors. It does not access the network, download GEO files, run analysis, create task results, create artifacts, or write execution logs.

## GPL570 Annotation Parser Design

The next readiness layer should inspect a locally provided GPL570-style platform annotation fixture and produce a probe-to-symbol mapping report. This is a parser/readiness design only; it does not download GPL570, query GEO, run DEG, or modify `geo_workflow.py`.

Minimum input forms:

- a local platform annotation text/CSV/TSV fixture with probe id and gene symbol columns.
- optional aliases for common Affymetrix/GEO columns such as `ID`, `ID_REF`, `Probe Set ID`, `Gene Symbol`, `Gene symbol`, `GENE_SYMBOL`, and `Symbol`.
- fake/minimal fixtures for unit tests before any real GPL570 file is inspected.

Minimum report fields should include:

- platform id, expected `GPL570` for the first controlled GSE33630 path.
- probe count.
- mapped probe count.
- unmapped probe count.
- duplicated symbol count.
- mapping success rate.
- acceptable yes/no.
- warnings and errors.

Parser behavior:

- identify the probe id column.
- identify the gene symbol column.
- strip empty symbols and common placeholder values.
- split multi-symbol cells only when the delimiter strategy is explicit; the first foundation can use the first non-empty symbol and warn.
- count duplicated target symbols because multiple probes may map to one gene.
- mark mapping unacceptable if success rate is below a conservative threshold.
- never infer biology from probe ids alone.

Preflight integration design:

- `AnalysisPreflightSummary` should continue to accept metadata and expression reports independently.
- a future `PlatformAnnotationMappingReport` can be passed into the GEO Series Matrix preflight helper.
- if platform mapping is acceptable, the GPL570/probe mapping blocker can be cleared.
- if platform mapping is missing or unacceptable, DEG preflight remains blocked or warning-only according to the explicit policy implemented in the bridge.

Boundaries:

- no real GPL570 download in this design task.
- no production downloader changes.
- no DEG, enrichment, or survival.
- no full expression matrix persistence.
- no GEO/TCGA/GTEx integration changes.
- no `geo_workflow.py` changes.

Next minimal implementation should add a small report model and fake-fixture parser, then wire the report into preflight without touching DEG execution.

## GPL570 Annotation Readiness Manual-Test Plan

The next controlled GSE33630 readiness step can use a manually supplied local GPL570 annotation file to test `PlatformAnnotationMappingReport`. The planned test should record platform id, local annotation file path, probe id column, gene symbol column, probe count, mapped/unmapped probe counts, duplicated symbol count, mapping success rate, acceptable status, warnings, errors, manual correction needs, and final decision.

This plan does not authorize downloading GPL570, parsing a real GPL570 file, running DEG, changing production downloader behavior, or modifying `geo_workflow.py`.

## v0.35 GPL570 Mapping Readiness Baseline

The GPL570 mapping readiness foundation is now documented and implemented at fake/local fixture level. The readiness chain can represent platform annotation mapping counts and can clear the default probe mapping readiness blocker when an acceptable `PlatformAnnotationMappingReport` is supplied.

This baseline does not include real GPL570 download, real GPL570 file parsing, DEG, enrichment, survival, production downloader changes, or `geo_workflow.py` changes. The next controlled action requires a manually supplied GPL570 annotation file or a separate real GPL570 format audit.

## GPL570 Manual File First Parser Check

The first local GPL570 annotation parser check used the manually supplied untracked file `tests/geodatabase/GPL570-55999 (1).txt`. The current parser returned `probe_id_column_missing` and `gene_symbol_column_missing` because the file begins with comment metadata and the real table header starts later.

Manual inspection found the table header at line 17, beginning with `ID` and including `Gene Symbol`. The next controlled implementation should harden the parser to detect that header while continuing to avoid downloads, DEG, production downloader changes, and `geo_workflow.py` changes.

## GPL570 Annotation Parser Retest

After header detection hardening, the local manual GPL570 annotation file parses successfully. The parser detects the `ID` probe column and `Gene Symbol` symbol column, reports 54675 probes, 45782 mapped probes, 8893 unmapped probes, 22902 duplicated gene-symbol targets, and a mapping success rate of 0.8373. The report is acceptable, with warnings for multi-symbol collapse and duplicated symbols, and no errors.

This clears the GPL570 probe-to-symbol blocker at mapping-report level. The GPL570 file remains untracked, and no DEG, enrichment, survival, production downloader change, or `geo_workflow.py` change was performed.

## GSE33630 Preflight After GPL570 Mapping

With the local Series Matrix expression report and local GPL570 mapping report supplied, GSE33630 preflight is runnable at readiness level. `expression_matrix_values_not_parsed` is cleared, GPL570 probe-to-symbol mapping is acceptable, sample mapping is matched, and the PTC vs normal/control candidate has 49 case samples and 45 control samples. Remaining blocking errors: none.

Warnings remain for multi-symbol collapse, duplicated symbols, ATC exclusion, and candidate comparison detection. No DEG, enrichment, survival, production downloader change, or `geo_workflow.py` change was performed.

## GSE33630 DEG Runner Readiness Decision

GSE33630 now satisfies readiness conditions for a DEG runner design audit: expression values are report-checked, sample ids match, PTC vs normal/control grouping is available, ATC samples are excluded, and GPL570 probe-to-symbol mapping is acceptable.

This decision does not implement or run a DEG runner. The next appropriate task is a design audit for a minimal GSE33630 DEG runner path, with explicit review of statistical engine choice, inputs, outputs, result registration, artifacts, and safety boundaries.

Still excluded: limma/DESeq2/edgeR execution, enrichment, survival, production downloader changes, and `geo_workflow.py` changes.

## GSE33630 DEG Runner Design Audit

The DEG runner design audit recommends a DEG-ready matrix builder as the next implementation step. This avoids adding heavy statistical dependencies and avoids claiming formal DEG results before engine policy is decided.

The proposed first scope is GSE33630-like Series Matrix input, PTC vs normal/control only, GPL570 probe-to-symbol mapping, and mean collapse reporting. No DEG, enrichment, survival, production downloader change, or `geo_workflow.py` change is implemented by this audit.

## GSE33630 DEG-Ready Matrix Manual Test Plan

The next controlled manual test can evaluate DEG-ready matrix preparation for GSE33630 without running DEG. Current prerequisites are present: expression values report, group labels, and acceptable GPL570 mapping.

The test should read local Series Matrix expression rows, apply GPL570 mapping, collapse duplicated symbols with the declared strategy, and record feature count, mapped feature count, gene count, sample count, case/control counts, duplicated gene count, ready status, warnings, and errors. No formal statistics should be run.

## v0.36 GSE33630 DEG Readiness Baseline

The v0.36 baseline records GSE33630 as DEG-ready at the readiness/reporting layer, not at the formal analysis layer:

- preflight runnable: yes.
- GPL570 mapping acceptable: yes.
- DEG-ready matrix builder foundation: present.
- expected comparison: PTC vs normal/control.
- excluded group: ATC.

No formal DEG statistics are implemented or run. There is still no limma, DESeq2, edgeR, enrichment analysis, production downloader change, or `geo_workflow.py` change.

The next controlled action should be either:

- a real GSE33630 DEG-ready matrix manual test with local untracked files.
- a minimal two-group DEG statistical runner audit before any statistical dependency is introduced.

## GSE33630 DEG-Ready Matrix Manual Test Scope

The next manual readiness test is scoped to two existing local files:

- `tests/geodatabase/GSE33630_series_matrix.txt.gz`
- `tests/geodatabase/GPL570-55999 (1).txt`

The expected output is a DEG-ready matrix report with feature count, mapped feature count, unmapped feature count, duplicated gene count, gene count after collapse, case/control counts, collapse strategy, ready status, warnings, and errors.

The test should confirm that GPL570 mapping can be applied to the expression report and that the PTC vs normal/control sample grouping remains PTC = 49 and normal/control = 45.

The test remains readiness-only. It must not compute p-values, formal logFC, enrichment, survival, or a DEG result table, and it must not change downloader code or `geo_workflow.py`.

## GSE33630 DEG-Ready Matrix Manual Report

The controlled local-file test produced a DEG-ready matrix report without writing a full matrix artifact and without running formal DEG statistics:

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

The readiness result supports a next audit for a minimal two-group DEG statistical runner. It does not authorize running limma, DESeq2, edgeR, enrichment, survival, production downloader changes, or `geo_workflow.py` changes.

## GSE33630 DEG-Ready Matrix Baseline

The controlled GSE33630 DEG-ready matrix baseline is ready at report level:

- expression matrix values are connected.
- PTC vs normal/control sample groups are connected.
- GPL570 probe-to-symbol mapping is connected.
- feature count: 54675.
- mapped feature count: 45782.
- unmapped feature count: 8893.
- gene count after collapse: 22880.
- case count: 49.
- control count: 45.
- collapse strategy: `mean`.
- ready: yes.

Still excluded: formal DEG statistics, p-values, formal logFC, limma/DESeq2/edgeR, enrichment, production downloader changes, and `geo_workflow.py` changes.

Next recommendation: minimal two-group DEG statistical runner audit.

## Minimal Two-Group DEG Runner Design

The first statistical runner design should stay limited to the GSE33630 PTC vs normal/control comparison and should consume only DEG-ready inputs: gene-level matrix values, group labels, and the readiness report.

If no new dependency is introduced, the runner should be effect-size-only:

- case mean.
- control mean.
- mean difference.
- log2FC summary with documented pseudocount.
- `DegResultSummary`.
- `deg_result_table.csv` without p-value or FDR columns.

The standard library is not sufficient for a complete t-test plus multiple-testing correction policy at production quality. If formal p-values, adjusted p-values, or a volcano-ready table are required, the next step must be a dedicated scipy/statsmodels dependency audit.

Still out of scope: limma, DESeq2, edgeR, enrichment, survival, batch correction, production downloader changes, and `geo_workflow.py` changes.

## GSE33630 Minimal DEG Summary Manual Test Plan

GSE33630 currently has DEG-ready matrix `ready=yes`. The next manual test can compute an exploratory mean log2FC summary from a gene-level collapsed matrix.

The test should record gene count, computed gene count, skipped gene count, top absolute log2FC genes, warnings, and errors. It must not calculate p-values or FDR and must not present the output as a formal DEG result.

The output label should be exploratory DEG summary. Enrichment, survival, production downloader changes, and `geo_workflow.py` changes remain out of scope.

## GSE33630 Exploratory Minimal DEG Summary Manual Test

The real local files were used read-only to build the collapsed gene-level matrix and compute an exploratory mean/log2FC summary. The manual test did not write a full DEG table into the repository and did not compute p-values or FDR.

Summary:

- gene-level collapsed matrix built: yes.
- gene count: 22880.
- computed gene count: 22880.
- skipped gene count: 0.
- case count: 49.
- control count: 45.
- collapse strategy: `mean`.
- pvalue available: false.
- FDR available: false.
- top absolute log2FC genes: `RP11-476D10.1`, `MMRN1`, `PRR15`, `ARHGAP36`, `ZCCHC12`, `LRP1B`, `RXRG`, `TMEM255A`, `GABRB2`, `PDZRN4`.
- warnings: `multi_symbol_cells_collapsed_to_first`, `duplicated_symbols_detected`, `duplicated_genes_collapsed`, `unmapped_probes_excluded`.
- errors: none.

This remains an exploratory DEG summary, not a formal DEG result.

## Formal DEG Statistical Dependency Audit

The exploratory GSE33630 mean/log2FC summary has no p-value, no FDR, no variance model, no empirical Bayes moderation, and no formal significance calls. It is useful for descriptive inspection only.

A formal DEG runner would require a defined two-group statistical test, multiple-testing correction, logFC semantics, p-value, adjusted p-value, and clear result-table policy.

Dependency options:

- no new dependency: continue descriptive summaries only.
- scipy: possible basic statistical tests, subject to separate audit.
- statsmodels: possible multiple-testing correction, subject to separate audit.
- rpy2/limma: not recommended now due to heavier environment coupling.

Recommendation: do not change requirements or implement formal DEG in this phase. Audit scipy/statsmodels first if formal p-values and FDR are required.

## v0.37 Minimal DEG Summary Foundation

The v0.37 baseline records the standard-library minimal DEG summary layer. It can compute mean/log2FC summaries from fake gene-level matrices and write an effect-size-only CSV artifact. It does not compute p-values, adjusted p-values, formal significance calls, enrichment, survival, or limma/DESeq2/edgeR output.

Next controlled options are GSE33630 real minimal DEG summary manual test, scipy/statsmodels dependency audit, or formal DEG runner design.

## v0.38 GSE33630 Exploratory DEG Summary Baseline

The v0.38 baseline records the controlled read-only GSE33630 exploratory mean/log2FC summary manual test and the formal DEG dependency audit.

Current result:

- gene-level collapsed matrix built: yes.
- gene count: 22880.
- computed gene count: 22880.
- skipped gene count: 0.
- case count: 49.
- control count: 45.
- collapse strategy: `mean`.
- pvalue available: false.
- FDR available: false.

This is still descriptive only. It is not formal DEG and does not include p-values, adjusted p-values, limma/DESeq2/edgeR output, enrichment, survival, production downloader changes, or `geo_workflow.py` changes.

The dependency audit recommends a separate scipy/statsmodels decision before changing requirements or implementing formal DEG statistics. Next choices are minimal formal DEG with reviewed dependencies, continued no-dependency descriptive summaries, or a volcano-ready descriptive table without p-values.

## Volcano-Ready Descriptive Table Design

The no-dependency volcano-ready table is a descriptive export from `DegSummaryReport.rows`. It is intended for exploratory plotting compatibility, not formal significance analysis.

Output: `volcano_ready_descriptive_table.csv`

Columns:

- `gene_symbol`
- `case_mean`
- `control_mean`
- `log2fc`
- `abs_log2fc`
- `status`
- `pvalue`
- `padj`
- `pvalue_available`
- `fdr_available`
- `method`

`pvalue` and `padj` remain empty. `pvalue_available=false`, `fdr_available=false`, and `method=descriptive_mean_log2fc`. Any UI or report consuming this table must show exploratory/descriptive-only labeling and must not expose significance cutoffs based on this table.

## GSE33630 Descriptive Volcano Table Test

The current GSE33630 exploratory log2FC summary can produce the descriptive volcano-ready table shape. The controlled test records the table as generatable but does not commit the full table and does not draw a plot.

Recorded values:

- total genes: 22880.
- computed genes: 22880.
- skipped genes: 0.
- local artifact path: `<local-temp>/volcano_ready_descriptive_table.csv` (not committed).
- pvalue available: false.
- FDR available: false.
- no formal DEG.
- no significance claim.

Top absolute log2FC genes are limited to the existing exploratory top 10: `RP11-476D10.1`, `MMRN1`, `PRR15`, `ARHGAP36`, `ZCCHC12`, `LRP1B`, `RXRG`, `TMEM255A`, `GABRB2`, and `PDZRN4`.

## v0.39 Descriptive Volcano Table Baseline

The v0.39 baseline records a no-dependency descriptive volcano table path for the GSE33630 exploratory summary. It can emit the expected volcano table columns, including `abs_log2fc`, while leaving `pvalue` and `padj` empty.

The table remains exploratory/descriptive only:

- no p-value.
- no FDR.
- no formal DEG.
- no statistical significance thresholds.
- no scipy/statsmodels.
- no limma/DESeq2/edgeR.
- no enrichment or survival.
- no production downloader changes.
- no `geo_workflow.py` changes.

Next controlled decision: whether formal DEG should add scipy/statsmodels or remain descriptive-only.

## Formal DEG Dependency Decision

The current GSE33630 descriptive summary and volcano-ready table are not formal DEG. They have no p-value, no FDR, no variance model, and no formal differential-expression call.

Formal two-group DEG would require a statistical test, log2FC, p-value, adjusted p-value, and a stable output table. Dependency choices are:

- no new dependency: continue descriptive-only output.
- scipy: candidate for `ttest_ind` or `mannwhitneyu`.
- statsmodels: candidate for `multipletests` FDR correction.
- rpy2/limma: not recommended for the next step due to R runtime coupling.
- DESeq2/edgeR: not recommended for the next step because count-model and R workflow policy need separate design.

Recommendation: if formal DEG is approved, add scipy and statsmodels together in a dedicated dependency-management task before implementing a formal two-group runner. If new dependencies are not approved, continue descriptive reporting and UI.

This audit does not modify requirements, install packages, or run true statistical DEG.

## v0.40 Real Dataset Harness Baseline

The Real Dataset Test Harness MVP is now the controlled path for local-file real GEO readiness testing. It uses `RealDatasetReadinessReport`, `RealDatasetGap`, and `scripts/run_real_geo_readiness_test.py` to connect saved metadata, Series Matrix readiness, group detection, platform mapping, analysis preflight, and gap classification.

The controlled GSE33630 harness smoke result is:

- recommended action: `ready_for_manual_review`.
- gap count: 0.
- preflight runnable: true.
- feature count: 54675.
- sample count: 105.
- mapping success rate: 0.8373.
- detected groups: `['ptc', 'normal']`.
- excluded ATC samples: 11.

The harness remains a readiness/test mechanism, not a production downloader. It does not download GEO files, run formal DEG, run enrichment, run survival, create task results, create artifacts, create execution logs, automatically scan datasets, or modify `geo_workflow.py`.

Next controlled work should either add a read-only UI summary for harness reports or run GSE60542/GSE27155 local-file tests after manual files are provided.

## Next Dataset Decision Brief

The next real-dataset test should be selected by coverage need:

| option | focus | required local files | risk | expected benefit |
| --- | --- | --- | --- | --- |
| GSE60542 | primary/metastasis/N0-N1 grouping | saved GEO metadata, Series Matrix, optional platform annotation | grouping may require manual confirmation and may not map to a simple case/control rule | expands coverage to complex clinical/sample metadata |
| GSE27155 | multi-pathology and platform annotation | saved GEO metadata, Series Matrix, platform annotation | multi-class labels may block comparison readiness until a target subgroup is selected | expands coverage to multi-class filtering and platform mapping |
| Continue GSE33630 | formal DEG dependency decision or descriptive demo polish | existing local Series Matrix and GPL570 annotation | formal DEG requires explicit scipy/statsmodels approval | deepens a known-ready benchmark |

Recommendation: choose GSE60542 next if the goal is parser/readiness hardening across new failure modes. Choose GSE27155 if platform/multi-class annotation is the priority. Choose GSE33630 only if the next decision is whether to approve formal DEG dependencies or improve demo output.

No option authorizes automatic downloads, production downloader changes, formal DEG, enrichment, survival, or `geo_workflow.py` changes.

## GSE60542 Local-File Harness Inspection

The first local-file GSE60542 readiness inspection used manually supplied untracked files:

- `tests/geodatabase/GSE60542_series_matrix.txt.gz`
- `tests/geodatabase/GPL570-55999 (1).txt`

The provided `tests/geodatabase/GSE60542_family.soft.gz` file remains local-only and was not passed as `--metadata-file` because the current harness metadata path expects saved plain text/HTML, not compressed SOFT.

Command attempted:

```bash
python3 scripts/run_real_geo_readiness_test.py \
  --dataset-id GSE60542 \
  --series-matrix-file tests/geodatabase/GSE60542_series_matrix.txt.gz \
  --platform-annotation-file "tests/geodatabase/GPL570-55999 (1).txt" \
  --json
```

Readiness result:

- feature count: 54675.
- matrix sample count: 92.
- Series Matrix sample count: 92.
- platform id: `GPL570`.
- matrix numeric value status: `numeric`.
- missing value count: 0.
- sample id match status: `match`.
- platform mapping acceptable: true.
- mapping success rate: 0.8373.
- mapped probes: 45782.
- unmapped probes: 8893.
- detected groups: `normal`, `ptc`.
- comparison candidate: PTC vs normal.
- comparison readiness: runnable, with 36 PTC samples and 34 normal samples.
- preflight runnable: true.

Initial gap:

- `group_detection_gap`: `ambiguous_samples`.
- ambiguous sample count: 22.
- ambiguous categories observed from sample titles/source names include lymph node metastasis (`LNM`), recurrence (`R`), and related N1 subgroup labels.
- recommended action from harness: `review_group_detection`.

Interpretation:

GSE60542 is behaving as the complex grouping benchmark. The expression matrix, sample matching, platform mapping, and base PTC-vs-normal preflight are usable, but the dataset also contains metastasis/recurrence/N0-N1 semantics that require an explicit comparison policy before parser behavior should be changed.

No GEO/GPL files were downloaded, no local real files were committed, no formal DEG/enrichment/survival was run, no production downloader was changed, and `geo_workflow.py` was not modified.

Decision required before code changes:

- Treat LNM/recurrence samples as excluded groups for a PTC-vs-normal comparison.
- Or design a separate primary tumor vs lymph node metastasis readiness comparison.
- Or design N0 vs N1 subgroup readiness for PTC/normal samples.

## GSE60542 PTC-vs-Normal Group Exclusion Retest

The first follow-up chose the conservative PTC-vs-normal scope: lymph node metastasis and recurrence samples are excluded from this candidate comparison rather than treated as normal/control, PTC, or ambiguous.

Implementation behavior:

- sample labels containing `LNM`, `lymph node metastasis`, or recurrence markers are classified as `excluded_non_target`.
- exclusion is based on `title` / `source_name_ch1` labels only.
- generic clinical fields such as `largest.dimension.ln.metastasis..cm.` do not exclude otherwise valid PTC or normal samples.
- excluded non-target samples generate readiness warnings but no `group_detection_gap`.

Retest result with the same local untracked files:

- feature count: 54675.
- matrix sample count: 92.
- sample id match status: `match`.
- platform mapping acceptable: true.
- mapping success rate: 0.8373.
- detected groups: `normal`, `ptc`.
- excluded non-target samples: 24.
- ambiguous samples: 0.
- gap count: 0.
- comparison candidate: PTC vs normal.
- comparison readiness: runnable, with 34 PTC samples and 34 normal samples.
- preflight runnable: true.
- recommended action: `ready_for_manual_review`.

The PTC-vs-normal path is now usable for readiness/manual review. Separate primary-vs-LNM or N0-vs-N1 comparisons still require their own scoped design and should not be inferred from this exclusion policy.

## GSE60542 PTC-vs-Normal Readiness Baseline

GSE60542 is complete for the selected PTC-vs-normal readiness path:

- local Series Matrix expression report is usable.
- GPL570 mapping is acceptable.
- sample ids match between expression matrix and Series Matrix metadata.
- PTC and normal groups are detected.
- LNM/recurrence samples are excluded as non-target samples for this comparison.
- ambiguous samples are cleared.
- gap count is 0.
- preflight is runnable.

Baseline values:

- feature count: 54675.
- sample count: 92.
- PTC samples in comparison: 34.
- normal samples in comparison: 34.
- excluded non-target samples: 24.
- mapping success rate: 0.8373.
- recommended action: `ready_for_manual_review`.

Still not implemented or not claimed:

- no formal DEG.
- no enrichment or survival.
- no production downloader changes.
- no automatic GEO download.
- no `geo_workflow.py` changes.
- no primary-vs-LNM comparison.
- no N0-vs-N1 subgroup comparison.

The next dataset-level action is GSE27155 local-file readiness inspection. If GSE60542 is revisited later, it should be through a new scoped design for primary-vs-LNM or N0-vs-N1 readiness.

## GSE27155 SOFT Metadata Path

`GSE27155` is the next selected controlled readiness dataset. The local file currently available for this dataset is a GEO family SOFT archive (`family.soft.gz`), not a Series Matrix file.

The first supported path is local-file and read-only:

- parse SOFT series metadata.
- parse per-sample title/source/characteristics metadata.
- parse per-sample SOFT sample-table expression readiness statistics.
- parse embedded SOFT platform annotation mapping readiness.
- run group detection on sample metadata.
- emit a real-dataset readiness report.

Current boundary:

- no full expression matrix artifact output.
- no DEG, enrichment, or survival analysis.
- no production downloader changes.
- no `geo_workflow.py` changes.

The expected first result may remain blocked by expression readiness or gene mapping readiness until a scoped Series Matrix/expression or GPL96 mapping task is approved.

The first SOFT inspection found that `GSE27155` uses multi-class labels such as follicular thyroid carcinoma, follicular thyroid adenoma, oncocytic thyroid carcinoma/adenoma, medullary thyroid carcinoma, papillary thyroid carcinoma, normal thyroid, and anaplastic thyroid carcinoma. It also uses `morphology of papillary carcinomas: NA` fields on non-PTC samples.

The group detector now avoids treating the `morphology of papillary carcinomas` field name as PTC evidence when the value is `NA`, and excludes known non-target disease classes from the PTC-vs-normal candidate. This keeps the metadata-only inspection focused on PTC vs normal while preserving the need for manual comparison confirmation for any multi-class analysis.

## GSE27155 Local SOFT Readiness Inspection

The first local-file GSE27155 readiness inspection used the manually supplied untracked file:

- `tests/geodatabase/GSE27155_family.soft.gz`

Command:

```bash
python3 scripts/run_real_geo_readiness_test.py \
  --dataset-id GSE27155 \
  --soft-file tests/geodatabase/GSE27155_family.soft.gz \
  --json
```

Result:

- SOFT metadata parsed successfully.
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
- PTC samples: 51.
- normal samples: 4.
- excluded non-target samples: 44.
- ambiguous samples: 0.
- comparison candidate: PTC vs normal.
- preflight runnable: true.
- gap count: 0 from the current harness classifier.

Interpretation:

GSE27155 is now covered for SOFT metadata parsing, SOFT expression readiness reporting, embedded GPL96 mapping readiness, and multi-class group filtering. The PTC-vs-normal candidate can be identified, expression values are numeric with matched sample ids, and GPL96 mapping is acceptable.

This result makes GSE27155 suitable as a multi-class/platform readiness benchmark. The PTC-vs-normal/control comparison is a valid readiness comparison candidate, but the normal/control arm has only 4 samples. That small-control condition should be shown as a warning in readiness reports and should keep GSE27155 out of the primary formal DEG demonstration role.

This is not a formal DEG-ready decision yet. The multi-class comparison policy still requires manual confirmation, and GSE33630 remains the stronger default benchmark for PTC-vs-normal DEG demonstration.

Next scoped options:

- add a small-control warning policy for the default PTC-vs-normal comparison with 4 normal controls.
