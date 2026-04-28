# Real GEO Dataset Readiness Design

This audit defines the minimum readiness checks needed before real GEO data is used for analysis. It is documentation only. It does not implement a GEO DEG runner, download real GEO data, change `geo_workflow.py`, or connect a production downloader.

## Problem Areas

Real GEO data can fail before analysis for reasons that are not visible from a dataset id alone:

- GEO download candidates can be wrong or incomplete. A dataset may expose series matrix files, supplementary files, raw archives, platform annotations, or unrelated attachments, and the most convenient file is not always the correct analysis input.
- File names are not reliable. A file name can mention normalized expression, raw counts, platform ids, or sample groups without actually containing the expected content.
- Supplementary files, series matrix files, and raw archives are easy to confuse. Series matrix files may contain useful phenotype metadata but not the preferred expression matrix; supplementary archives may contain several matrix-like files or raw files that require a separate processing path.
- Expression matrix identification is risky. Candidate files need checks for tabular shape, feature rows, sample columns, numeric expression values, duplicate feature ids, and suspicious one-column or metadata-only tables.
- Sample annotation can be incomplete. Group labels, disease status, treatment labels, tissue source, time point, and platform/sample identifiers may be missing, inconsistent, or encoded in free text.
- Gene identifier mapping can be lossy. GEO data may use probe ids, gene symbols, Ensembl ids with versions, Entrez ids, mixed identifiers, or platform-specific ids that need explicit mapping and duplicate handling.
- Sample id alignment can fail. Expression matrix columns may not match metadata rows because of GSM aliases, title fields, prefixes, suffixes, or duplicate sample ids.
- Group/comparison detection can be ambiguous. Case/control groups may be absent, too small, free-text encoded, inverted, or mixed with batch/platform labels.

## Analysis Preflight Checks

A future analysis preflight layer should report readiness before any DEG or downstream analysis is run:

- dataset asset readiness: expression matrix, sample annotation, platform annotation, gene annotation, clinical annotation
- expression matrix readiness: row/column shape, numeric value coverage, duplicate features, missing sample columns, suspicious file type
- gene mapping readiness: input identifier type, target identifier type, mapping success rate, unmapped features, duplicated targets, collapse strategy
- sample mapping readiness: matrix sample count, metadata sample count, matched samples, unmatched matrix samples, unmatched metadata samples, duplicate sample ids
- comparison readiness: group column existence, case/control labels, case count, control count, missing group assignments, minimum sample counts
- runnable summary: blocking errors, warnings, recommended user action, and whether the analysis is safe to proceed

Gene mapping warnings should not always block analysis. For example, a moderate number of unmapped genes may be acceptable if the mapping rate is high and duplicate targets have a declared collapse strategy. Missing expression matrix, unusable sample alignment, or missing case/control groups should block the analysis preflight.

## UI Readiness Display

The UI should show readiness as read-only status before real analysis:

- dataset id and selected profile id
- expression matrix status
- sample annotation status
- gene/platform annotation status
- sample mapping match rate
- gene mapping success rate
- comparison runnable status
- blocking error count
- warning count
- recommended action

Warnings should explain the condition and the next user action. Blocking errors should be explicit, but the readiness layer itself should not execute analysis, download data, mutate workflows, or change `geo_workflow.py`.

## Practical Test Recording

When real GEO readiness tests are later run, each dataset review should record:

- dataset id
- candidate files reviewed
- selected expression matrix candidate
- selected sample metadata source
- selected platform/gene annotation source
- detected identifier type
- gene mapping success rate
- sample mapping match rate
- comparison rule and group counts
- blocking errors
- warnings
- user action needed
- whether the dataset is preflight-runnable

The first practical tests should stop at readiness. They should not run DEG, schedule tasks, or connect production downloads.

## Next Minimal Implementation

Recommended implementation order:

1. Add a dataset asset readiness model that evaluates fake asset metadata.
2. Add gene mapping readiness based on provided identifiers and fake mapping results.
3. Add sample mapping readiness for matrix columns and sample metadata ids.
4. Add comparison readiness for case/control group availability.
5. Combine those reports into an analysis preflight summary.
6. Register an analysis preflight summary as a read-only task result.
7. Surface the registered preflight summary in the existing UI summary area.

Each step should use fake/temp fixtures, avoid real GEO/TCGA data dependencies, avoid production downloaders, and keep `geo_workflow.py` unchanged.

## Dataset Asset Readiness Foundation

`DatasetAssetReadinessReport` is the first implementation step. It summarizes whether a dataset has the minimum asset categories needed before analysis preflight:

- expression matrix
- sample annotation
- platform annotation
- gene annotation
- clinical annotation

Asset statuses are `present`, `missing`, `partial`, `suspicious`, and `not_applicable`. Missing expression matrix is a blocking error. Missing sample or gene annotation is currently reported as a warning so the next mapping/preflight layers can decide whether the dataset should be blocked. Suspicious and partial assets are warnings.

`build_dataset_asset_readiness_report(dataset_id, assets)` only evaluates caller-provided fake asset metadata. It does not inspect real GEO files, download data, run analysis, or mutate workflow state.

## Gene Mapping Readiness Foundation

`GeneMappingReadinessReport` summarizes whether feature identifiers can be mapped before analysis. It records input id type, target id type, total features, mapped/unmapped counts, duplicate target count, mapping success rate, collapse strategy, warnings, errors, and acceptability.

`build_gene_mapping_readiness_report(...)` uses only caller-provided identifiers and fake mapping results. It can strip Ensembl version suffixes such as `ENSG000001.5 -> ENSG000001`, reports probe-only identifiers as requiring platform mapping, warns on duplicated targets, and marks the report unacceptable when the mapping success rate is below the configured threshold.

This helper does not query external databases, download annotations, infer platform mappings from GEO, or run analysis.

## Sample Mapping Readiness Foundation

`SampleMappingReadinessReport` checks whether expression matrix sample ids align with sample metadata ids. It reports matrix sample count, metadata sample count, matched sample count, unmatched matrix samples, unmatched metadata samples, duplicate sample ids, match rate, warnings, errors, and acceptability.

`build_sample_mapping_readiness_report(matrix_samples, metadata_samples)` uses caller-provided sample id lists only. It does not inspect real GEO files, infer GSM aliases, mutate metadata, or run analysis. A low match rate is blocking; extra or unmatched samples and duplicate ids are reported explicitly for review.

## Comparison Readiness Foundation

`ComparisonReadinessReport` checks whether a case/control comparison is usable before analysis. It records the comparison id, group column, case/control labels, case count, control count, samples missing group assignments, total samples, warnings, errors, and runnable status.

`build_comparison_readiness_report(sample_metadata, comparison_rule)` uses fake/sample metadata dictionaries and an explicit comparison rule. It reports missing group columns, missing case/control groups, small group sizes, and samples without group assignments. It does not run DEG, infer free-text group labels, call Module 5 execution, or depend on real GEO data.

## Analysis Preflight Summary Foundation

`AnalysisPreflightSummary` combines dataset asset readiness, gene mapping readiness, sample mapping readiness, and comparison readiness into one pre-analysis report. It records the dataset id, profile id, component reports, runnable status, blocking errors, warnings, and recommended action.

`build_analysis_preflight_summary(...)` does not execute analysis. It only aggregates existing readiness reports. Missing expression matrix, unacceptable sample mapping, unrunnable comparison, and unacceptable gene mapping become blocking errors. Non-blocking warnings are preserved so the UI can explain review actions before a user runs analysis.

## Analysis Preflight Result Registration

`TaskManagementService.register_analysis_preflight_result(...)` can register an `analysis_preflight_summary` task result. The result metadata records dataset id, profile id, runnable status, blocking error count, warning count, and recommended action.

Registration is result management only. It does not execute analysis, change `TaskRecord.state`, create a real analysis artifact, or require a production downloader. When no artifact path is provided, existing artifact diagnostics report the result as `not_applicable`.

## UI Read-Only Preflight Summary

Registered `analysis_preflight_summary` results are visible in the existing task results summary area. The UI reports dataset id, profile id, runnable status, blocking error count, warning count, recommended action, and result id.

The UI display is read-only. It does not generate a preflight summary, execute analysis, create a result, create an artifact, create an execution log, or modify workflow state.

## Practical GEO Readiness Protocol

`docs/practical_geo_readiness_test_protocol.md` defines the first manual readiness-test protocol for real GEO datasets. It covers simple matrix datasets, complex probe/platform datasets, and messy supplementary/metadata datasets. The protocol records candidate file review, asset readiness, gene mapping readiness, sample mapping readiness, comparison readiness, analysis preflight summary, UI summary, and user action needed.

The protocol intentionally stops before DEG analysis. It is a readiness test plan only.

## Smoke/Check Visibility

Smoke/check output includes an `Analysis preflight readiness summary` built from in-memory fake preflight summaries. It reports total checks, runnable checks, blocked checks, warning count, and blocking error count.

The smoke fixture is intentionally side-effect free: it does not download GEO data, execute analysis, create `TaskResultRecord` entries, create artifacts, or write execution logs.

## Fake GEO Preflight CLI

`scripts/run_fake_geo_preflight.py` runs the readiness/preflight chain against an in-memory fake GEO dataset fixture. It builds dataset asset readiness, gene mapping readiness, sample mapping readiness, comparison readiness, and the final analysis preflight summary.

Commands:

```bash
python3 scripts/run_fake_geo_preflight.py
python3 scripts/run_fake_geo_preflight.py --json
```

The command is a safe preflight-chain check. It does not read real GEO files, access the network, create `TaskResultRecord` entries, create artifacts, write execution logs, run DEG, or execute real analysis.

## Fake Preflight Baseline

The fake GEO preflight baseline verifies the readiness chain before any real GEO files are used:

- dataset asset readiness
- gene mapping readiness
- sample mapping readiness
- comparison readiness
- analysis preflight summary
- smoke/check readiness summary
- UI read-only display for registered preflight summaries

This baseline is a safety layer before practical GEO readiness testing. It uses fake/temp fixtures only, does not download real GEO data, does not execute analysis, does not create `TaskResultRecord` entries, and does not create artifacts or execution logs.

## v0.32 GEO Readiness Preflight Baseline

`v0.32-geo-readiness-preflight-baseline` records the current safe readiness layer:

- `DatasetAssetReadinessReport`
- `GeneMappingReadinessReport`
- `SampleMappingReadinessReport`
- `ComparisonReadinessReport`
- `AnalysisPreflightSummary`
- smoke/check analysis preflight readiness summary
- UI read-only display for registered `analysis_preflight_summary` results
- `scripts/run_fake_geo_preflight.py`
- quick developer-check coverage for the fake preflight CLI

The baseline still has no real GEO download, no production downloader, no DEG runner, no enrichment runner, and no `geo_workflow.py` changes. The next recommended step is a controlled practical GEO readiness test that records candidate files, mapping rates, comparison readiness, blocking errors, warnings, and user action needed before any real analysis is attempted.

## Controlled Real GEO Readiness Test Design

`docs/controlled_real_geo_readiness_test.md` defines the first controlled real GEO readiness test. It requires manual GSE selection before any real dataset work begins. The design uses three GSE classes: simple expression matrix, complex probe/platform annotation, and messy supplementary/sample metadata.

The controlled test records GSE id, disease/topic, expected groups, downloaded files, candidate expression matrix, sample metadata source, gene id type, sample id match rate, gene mapping success rate, comparison readiness, runnable status, blocking errors, warnings, and recommended user action.

Failure categories include download failure, no expression matrix, sample metadata missing, sample mismatch, gene mapping insufficient, comparison not runnable, file classification uncertain, and user confirmation required. The test still excludes DEG, enrichment, survival, TCGA/GTEx, production downloader changes, `geo_workflow.py` changes, scheduler behavior, and automatic task scanning.

## Selected PTC GEO Readiness Datasets

The first controlled PTC readiness dataset set is:

- `GSE33630`: simple/main PTC vs normal readiness test. Target checks are expression matrix readiness, sample metadata readiness, and PTC vs normal comparison readiness.
- `GSE60542`: complex clinical/sample grouping readiness test. Target checks are primary tumor, nodal metastasis, and N0/N1-style grouping readiness.
- `GSE27155`: multi-class/platform annotation readiness test. Target checks are PTC subgroup filtering, probe-to-symbol mapping, and platform annotation readiness.

The selected dataset set only authorizes documentation and readiness-log preparation at this stage. It does not authorize real GEO downloads, DEG, enrichment, survival analysis, production downloader changes, scheduler behavior, automatic task scanning, or `geo_workflow.py` changes.

## GSE33630 Dry-Run Readiness Checklist

`GSE33630` starts with a dry-run checklist before any file download. The checklist focuses on expression matrix candidate discovery, sample metadata source, PTC vs normal grouping, sample id match, gene/platform annotation, and final analysis preflight runnable status.

The checklist must record commands attempted, inspected files, detected asset type, mapping readiness, blocking errors, warnings, final readiness decision, and any tooling gap. If current software lacks a real GEO readiness CLI, that gap should be recorded explicitly. Do not implement downloader changes, modify `geo_workflow.py`, or run analysis as part of this checklist.

## GSE33630 Controlled Readiness Inspection

The first `GSE33630` inspection used only existing tooling and public GEO metadata. No real GEO files were downloaded, no production downloader was changed, and no analysis was run.

Observed public GEO metadata:

- Expression profiling by array dataset.
- Platform: GPL570 Affymetrix Human Genome U133 Plus 2.0 Array.
- Samples: 105 total, including 49 papillary thyroid carcinoma, 45 normal thyroid, and 11 anaplastic thyroid carcinoma samples.
- GEO exposes Series Matrix files, a large RAW CEL supplementary archive, and a small clinical annotation supplementary file.
- Processed data is reported as included within the sample table.

Readiness outcome:

- expression asset: candidate exists, but no expression matrix was downloaded or parsed.
- sample metadata: candidate exists via GEO sample table / Series Matrix, but no metadata table was parsed.
- gene/platform annotation: GPL570 identified, but probe-to-symbol mapping was not evaluated.
- sample mapping: not evaluated.
- comparison readiness: likely PTC vs normal candidate exists, but ATC samples must be excluded and labels must be parsed before runnable status can be confirmed.
- runnable: no for this pass.

Blocking issues:

- `expression_matrix_not_downloaded`
- `real_geo_readiness_cli_missing`

The software gap exposed by this pass is tooling, not analysis logic: current readiness helpers can evaluate provided assets and fake fixtures, but there is no real accession-level GEO readiness CLI that safely inspects `GSE33630` and feeds those assets into the preflight chain.

## GSE33630 Gap Analysis

`GSE33630` validates the need for a bridge between GEO accession metadata and the existing readiness models. It has enough public structure to serve as a simple benchmark, but the current software cannot yet convert that public structure into concrete preflight inputs.

Working areas:

- Metadata discovery can be documented without download or analysis.
- Candidate file roles can be identified manually from GEO page metadata.
- The fake preflight chain is available and side-effect free.
- Existing readiness report models are sufficient once expression, sample metadata, gene mapping, and comparison inputs are provided.

Current gaps:

- No real accession-level readiness CLI exists.
- No side-effect-free candidate asset inventory is generated for a GSE id.
- No Series Matrix parser is connected to readiness models.
- No sample metadata extraction is connected to sample mapping readiness.
- No GPL570 probe-to-symbol mapping readiness is computed from real platform/feature ids.
- No PTC vs normal comparison rule is inferred or confirmed from parsed metadata.
- No registered `analysis_preflight_summary` result exists for this real dataset.

Recommended next implementation should be narrow: a read-only real GEO readiness command that records accession metadata and candidate asset inventory first. It should not download large raw archives, run DEG, change production downloaders, mutate `geo_workflow.py`, or create task results automatically.

## Real GEO Accession Readiness CLI Design

The next narrow tooling layer should be `scripts/run_geo_accession_readiness.py`. Its purpose is candidate inventory, not data ingestion or analysis.

Initial command shape:

```bash
python3 scripts/run_geo_accession_readiness.py --gse GSE33630
python3 scripts/run_geo_accession_readiness.py --gse GSE33630 --json
```

The first stage should report:

- accession id
- title and summary, when available
- organism
- sample count
- platform ids
- Series Matrix candidate count and names
- supplementary file candidate count and names
- sample metadata candidate count and names
- expression candidate count and names
- warnings
- errors

The first stage must not:

- download large files
- download RAW archives
- run DEG
- run enrichment
- run survival
- modify production downloader logic
- modify `geo_workflow.py`
- create task results, artifacts, or execution logs

Stable failure handling should use explicit error codes:

- `network_unavailable`: metadata could not be fetched.
- `accession_not_found`: the requested accession is absent or invalid.
- `metadata_parse_failed`: metadata was retrieved or provided but could not be parsed.
- `no_expression_candidate`: no Series Matrix, processed sample table, or supplementary expression-like candidate was found.

Later phases can connect the inventory to `DatasetAssetReadinessReport` and `AnalysisPreflightSummary`, but the CLI should stay read-only and accession-scoped.

## GEO Accession Inventory Model

`GeoAccessionInventory` is the lightest structure for real accession metadata before any download or parsing of large files. It records:

- `gse_id`
- title and summary
- organism
- sample count
- platform ids
- Series Matrix candidates
- supplementary file candidates
- sample metadata candidates
- expression candidates
- warnings and errors

`GeoRemoteAssetCandidate` records one remote candidate with candidate type, name, URL, size hint, confidence, reasons, and warnings. The model is intentionally data-only and can be tested with fake metadata. It does not fetch GEO, download files, parse expression matrices, execute analysis, create task results, or mutate workflow state.

If no expression candidate is recorded, the inventory emits `no_expression_candidate` as a warning. Later readiness stages may promote that condition to a blocking error after file-discovery policy is finalized.

## GEO Accession Metadata Parser Foundation

`parse_geo_accession_metadata(text)` converts an already provided GEO-like metadata text fixture into `GeoAccessionInventory`. It extracts the accession id, title, summary, organism, sample count, platform ids, Series Matrix hints, supplementary file hints, sample metadata hints, and expression candidate hints.

The parser is intentionally local-input only. It does not access the network, download GEO files, parse expression matrices, parse FASTQ/BAM/CRAM content, execute analysis, create task results, or mutate workflow state. Malformed metadata returns a stable inventory with `metadata_parse_failed` in `errors` rather than failing at the UI or CLI boundary.

## Fake-Backed GEO Accession Readiness CLI

`scripts/run_geo_accession_readiness.py` provides the first read-only accession readiness command. In this stage it supports local metadata-file input:

```bash
python3 scripts/run_geo_accession_readiness.py --metadata-file <path>
python3 scripts/run_geo_accession_readiness.py --metadata-file <path> --json
```

The command reports accession id, sample count, platform ids, Series Matrix candidate count, supplementary candidate count, sample metadata candidate count, expression candidate count, warnings, and errors. It is fake-backed/local-file backed only: it does not fetch GEO metadata, download files, run DEG, create `TaskResultRecord` entries, create artifacts, write execution logs, or modify `geo_workflow.py`.

For `GSE33630`, this partially mitigates `real_geo_readiness_cli_missing`: the project now has a safe command boundary and parser for saved metadata. It does not resolve `expression_matrix_not_downloaded`; a future controlled pass still needs either live metadata fetch or manually saved metadata, followed by a separate explicit decision about whether to download and parse a small Series Matrix file.

## GSE33630 Saved Metadata CLI Result

The fake-backed/local-file CLI was tested with a saved official GEO HTML metadata file for `GSE33630` of approximately 47 KB. The test did not download Series Matrix, RAW, or supplementary data files.

The CLI identified `GSE33630`, `GPL570`, one Series Matrix candidate, two supplementary candidates, two sample metadata candidates, and two expression candidates, with zero warnings and zero errors.

The parser did not extract title, organism, summary, or sample count from the saved NCBI GEO HTML. Candidate inventory is therefore usable, but full HTML metadata field extraction remains a parser gap.

## GEO HTML Metadata Field Parser

`parse_geo_accession_metadata(text)` now normalizes common saved NCBI GEO HTML/text fixtures before extracting metadata. The parser supports title, summary, organism, sample count, platform ids, Series Matrix candidates, supplementary candidates, sample metadata candidates, and expression candidates from local input text.

Missing optional fields are reported as warnings such as `title_missing`, `summary_missing`, `organism_missing`, and `sample_count_missing`; malformed accession content reports `metadata_parse_failed`. The parser still does not access the network, download GEO data, parse large files, execute analysis, create results, create artifacts, write logs, or modify `geo_workflow.py`.

The GSE33630 saved HTML retest confirms that title, organism, summary, platform ids, Series Matrix candidates, supplementary candidates, sample metadata candidates, and expression candidates are extracted. The remaining parser gap is `sample_count_missing` for the actual NCBI GEO HTML layout. This is a metadata extraction issue only; expression matrix download and parsing remain out of scope.

The sample-count parser supports the NCBI GEO table label pattern `Samples (N)`, which appears in saved GSE pages such as `GSE33630`. If that label is absent, the parser keeps returning `sample_count=0` with `sample_count_missing` rather than failing.

The GSE33630 saved HTML retest now extracts `sample_count=105` with no parser warnings or errors. The remaining blocked readiness item is expression matrix download/parse, not accession metadata parsing.

## Real Dataset Harness Baseline

The v0.40 real dataset harness baseline records the local-file controlled readiness path for real GEO datasets. `RealDatasetReadinessReport` summarizes metadata parsing, Series Matrix metadata, expression reporting, group detection, platform mapping, and preflight. `RealDatasetGap` classifies failures into categories such as metadata parsing, Series Matrix parsing, expression matrix, sample mapping, gene mapping, group detection, comparison readiness, preflight, UI display, and manual confirmation.

`scripts/run_real_geo_readiness_test.py` is the current harness entry point. It accepts manually supplied local files and can emit JSON or Markdown reports, but it does not download GEO data and is not a production downloader.

The GSE33630 harness smoke is ready for manual review:

- gap count: 0.
- preflight runnable: true.
- feature count: 54675.
- sample count: 105.
- mapping success rate: 0.8373.
- detected groups: `['ptc', 'normal']`.
- excluded ATC samples: 11.

Still excluded: formal DEG, enrichment, survival, production downloader changes, automatic real dataset downloads, and `geo_workflow.py` changes. Next work is UI readiness report display and local-file testing for GSE60542/GSE27155.

## GSE60542 Readiness Baseline

GSE60542 is now passed for the selected PTC-vs-normal controlled readiness path. The local-file harness reports a numeric Series Matrix expression report, matched sample ids, acceptable GPL570 mapping, detected PTC and normal groups, 24 excluded LNM/recurrence non-target samples, zero ambiguous samples, zero gaps, and runnable preflight.

This baseline is readiness-only. It does not run formal DEG, enrichment, survival, production downloads, automatic GEO downloads, or `geo_workflow.py` changes. Primary-vs-LNM and N0-vs-N1 comparisons remain separate future designs.

## UI Read-Only Real Dataset Readiness Summary

The UI summary can now display a read-only `RealDatasetReadinessReport` summary when the application service provides a precomputed summary dictionary. The display includes dataset id, recommended action, gap count, preflight runnable status, feature count, sample count, mapping success rate, detected groups, excluded groups, blocking gaps, and warning count.

This UI path does not run `scripts/run_real_geo_readiness_test.py`, read `tests/geodatabase/`, download data, create `TaskResultRecord`, create artifacts, create execution logs, run formal DEG, or modify `geo_workflow.py`. Empty state remains stable when no report summary is loaded.

## Live GEO Metadata Fetch Design

The next minimal live step should be accession metadata fetch only. The command should fetch the NCBI GEO accession page HTML/text, pass the response to `parse_geo_accession_metadata(text)`, and output a `GeoAccessionInventory`.

Proposed command shape:

```bash
python3 scripts/run_geo_accession_readiness.py --gse GSE33630 --live
python3 scripts/run_geo_accession_readiness.py --gse GSE33630 --live --json
python3 scripts/run_geo_accession_readiness.py --gse GSE33630 --live --timeout 15
```

The live mode should only request the accession metadata page, for example the NCBI GEO `acc.cgi?acc=GSE...` page. It must not follow candidate links to download:

- Series Matrix files
- RAW archives such as `GSE*_RAW.tar`
- supplementary expression files
- FASTQ/SRA records
- platform annotation data files

Stable failure codes:

- `network_unavailable`
- `ssl_error`
- `accession_not_found`
- `fetch_timeout`
- `metadata_parse_failed`

This live metadata fetch is not a production downloader. It is a narrow readiness inventory helper with explicit `--live` opt-in, timeout control, stable errors, and no task/result/artifact/log creation. The next implementation should add a small fetch helper with mocked-network tests and keep the default CLI behavior local-file only.

## Live GEO Metadata Fetch Foundation

`fetch_geo_accession_metadata(gse_id, timeout=...)` fetches only the NCBI GEO accession metadata page and returns HTML/text for `parse_geo_accession_metadata(text)`. `scripts/run_geo_accession_readiness.py` supports explicit live mode:

```bash
python3 scripts/run_geo_accession_readiness.py --gse GSE33630 --live --json
python3 scripts/run_geo_accession_readiness.py --gse GSE33630 --live --timeout 15
```

Default CLI behavior remains local metadata-file mode. Live mode is opt-in and is tested with mocked network calls only. Network, SSL, timeout, and missing accession failures return stable error codes. The helper does not download Series Matrix, RAW archives, supplementary files, FASTQ/SRA files, create task results, create artifacts, write logs, run analysis, change production downloader code, or modify `geo_workflow.py`.

Live error reporting:

- `ssl_error`: local certificate/Python SSL verification failed.
- `network_unavailable`: network access failed before a usable HTTP response.
- `fetch_timeout`: metadata page fetch exceeded the configured timeout.
- `http_error`: NCBI returned a non-success HTTP response other than an accession-not-found classification.
- `accession_not_found`: the accession id is missing or not found.

CLI JSON output includes `errors`, `warnings`, and `recommended_action`. For `ssl_error`, the recommended action is to check the local certificate/Python SSL environment, use `--metadata-file` as the fallback, and avoid disabling SSL verification by default.

## GSE33630 Live Metadata Fetch Result

The first controlled live metadata fetch for `GSE33630` returned `ssl_error` due to certificate verification failure in the local environment. The command did not fetch parseable metadata and did not download Series Matrix, RAW, supplementary, FASTQ/SRA, or analysis files.

This result validates the stable failure surface for live metadata fetch. The recommended operational fallback is still `--metadata-file` until SSL/environment guidance is added or the live fetch environment is corrected.

## Post-Live GSE33630 Gap Analysis

The `GSE33630` live metadata attempt shows that the remaining blocker is live HTTPS access in the local environment. The accession parser already handles saved GSE33630 HTML metadata, including title, summary, organism, sample count, platform ids, Series Matrix candidates, supplementary candidates, sample metadata candidates, and expression candidates.

Readiness interpretation:

- live accession fetch: available, opt-in, and returning stable errors.
- current live result: blocked by `ssl_error`.
- parser status for saved metadata: adequate for accession-level candidate inventory.
- expression matrix status: still not downloaded or parsed.
- preflight status: still not runnable from real GEO assets.

Recommended next step:

- Prefer SSL/environment guidance or continue `--metadata-file` mode for the next controlled `GSE33630` pass.
- Do not start Series Matrix download/parse until the next task explicitly authorizes that narrower inspection step.

Preserved boundaries:

- no Series Matrix / RAW / supplementary download
- no DEG, enrichment, or survival analysis
- no production downloader changes
- no `geo_workflow.py` changes
- no task result, artifact, or execution log creation

## Live GEO Metadata SSL Guidance

The controlled `GSE33630 --live` metadata fetch is currently blocked by `ssl_error` in the local Python/certificate/network environment. This error means the HTTPS certificate chain could not be verified by the local runtime. It does not mean the GEO accession is missing, and it does not invalidate the saved-metadata parser.

Recommended fallback:

1. Open the official GEO accession page in a browser.
2. Save the accession metadata HTML/text locally.
3. Continue the controlled readiness test with:

```bash
python3 scripts/run_geo_accession_readiness.py --metadata-file <saved-geo-metadata.html> --gse GSE33630 --json
```

Do not bypass SSL verification by default. The live fetch path should remain a safe metadata-only helper that uses normal certificate verification. Future guidance may document how to repair the local Python certificate environment or how to configure trusted certificates explicitly, but it should not add an insecure default.

Current next-step options:

- A: fix the local certificate/Python SSL environment and retry `--live`.
- B: continue controlled readiness testing with `--metadata-file`.
- C: add configurable certificate guidance later, without defaulting to disabled verification.

This guidance does not authorize Series Matrix download/parse, RAW archive download, supplementary file download, production downloader changes, or `geo_workflow.py` changes.

## GSE33630 Metadata-File Path Status

For the current controlled readiness pass, `--metadata-file` is the active path. It can extract the following from saved official GSE33630 metadata:

- `GSE33630`
- `GPL570`
- title
- organism
- summary
- `sample_count=105`
- Series Matrix candidates
- supplementary candidates
- expression candidates

The `--live` path remains suspended by `ssl_error`. The next readiness decision is whether to design a Series Matrix metadata-only download/parse audit or continue with manually saved accession metadata. This section does not authorize downloading Series Matrix, RAW, supplementary files, or running any analysis.

## Series Matrix Metadata-Only Audit Scope

For `GSE33630`, the Series Matrix is the likely next candidate because accession metadata indicates processed data is included in GEO sample/series-level material. A metadata-only audit should precede any real file inspection.

The audit should define:

- candidate selection rules for Series Matrix files.
- maximum file-size and line-count limits for a future parser.
- expected metadata sections, including sample titles, source names, characteristics, platform ids, and sample ids.
- expression candidate signals, such as numeric feature rows and probe/sample table shape.
- group-label signals for PTC, normal thyroid, and ATC exclusion.
- failure classes, including `series_matrix_not_selected`, `series_matrix_too_large`, `sample_metadata_not_detected`, `expression_table_not_detected`, and `group_labels_uncertain`.

The audit should not download data, parse real files, execute analysis, create results, create artifacts, write logs, modify production downloader behavior, or change `geo_workflow.py`.

If approved later, implementation should start with fake/temp Series Matrix fixtures before any controlled real file is inspected.

## Series Matrix Metadata Parser Foundation

The first parser foundation is metadata-only. `parse_series_matrix_metadata(path_or_text)` accepts local text, local `.txt`, or local `.txt.gz` fixtures and extracts:

- `!Series_geo_accession`
- `!Series_platform_id` / `!Sample_platform_id`
- `!Sample_geo_accession`
- `!Sample_title`
- `!Sample_source_name_ch1`
- `!Sample_characteristics_ch1`

It returns `SeriesMatrixMetadataReport` with accession id, platform ids, sample ids, sample count, sample metadata columns, sample metadata rows, group hints, warnings, and errors. It stops before `!series_matrix_table_begin` and does not parse expression matrix numeric values.

The current foundation is tested only with fake/minimal fixtures. It does not download real GEO files, inspect the real GSE33630 Series Matrix, run analysis, create results, create artifacts, or modify `geo_workflow.py`.

## GEO Sample Group Detection Foundation

`detect_geo_sample_groups(...)` consumes metadata rows, such as rows produced by the Series Matrix metadata parser, and reports candidate group labels without creating a final comparison. The first foundation recognizes:

- papillary thyroid carcinoma / PTC / papillary carcinoma as `ptc`
- normal thyroid / normal as `normal`
- anaplastic thyroid carcinoma / ATC as an excluded candidate

The helper returns group column candidates, detected groups, sample-to-group labels, ambiguous samples, excluded candidates, confidence, warnings, and errors. ATC samples are kept out of the PTC vs normal candidate comparison. Ambiguous samples produce warnings.

Normal/control detection also covers common GEO wording such as `patient-matched non-tumor control`, `non-tumor control`, `non tumor control`, `matched non-tumor`, `non-tumoral`, `adjacent non-tumor`, `adjacent normal`, and `normal control`.

This remains readiness-only. It does not run analysis, create comparison records, download files, create results, or modify `geo_workflow.py`.

## Series Matrix Metadata-Only Preflight Bridge

`build_geo_series_matrix_preflight_summary(...)` connects `SeriesMatrixMetadataReport` and `GroupDetectionReport` to `AnalysisPreflightSummary`. This bridge is intentionally not runnable when only metadata is available:

- `expression_matrix_values_not_parsed` is recorded as a blocking error.
- PTC vs normal labels can be recorded as candidate comparison readiness.
- ATC samples can be preserved as excluded warnings.
- sample id alignment is checked only between metadata-derived sample ids and metadata rows.

The bridge does not parse expression values, run DEG, download files, create `TaskResultRecord`, create artifacts, write logs, or modify `geo_workflow.py`.

## GSE33630 Metadata-Only Implementation Status

The current metadata-only readiness layer now includes:

- saved GEO HTML accession metadata parsing.
- GSE33630 sample count extraction.
- `SeriesMatrixMetadataReport`.
- `parse_series_matrix_metadata(...)` for fake/local text, `.txt`, and `.txt.gz` fixtures.
- `GroupDetectionReport` and `detect_geo_sample_groups(...)`.
- `build_geo_series_matrix_preflight_summary(...)`.

This is not yet a real GSE33630 Series Matrix readiness test. The following remain explicitly incomplete:

- real GSE33630 Series Matrix file test.
- expression matrix numeric value parsing.
- GPL570 probe-to-symbol mapping.
- runnable DEG preflight.

Next choices are manual: provide a GSE33630 Series Matrix file for parser testing, audit expression value parsing, audit GPL570 annotation parsing, or continue to GSE60542 metadata-only readiness.

## GSE33630 Real Series Matrix Metadata-Only Retest

A manually supplied local `GSE33630_series_matrix.txt.gz` file was used for a read-only metadata parser retest. The file is local manual test data and is not committed.

Results:

- gzip read: yes
- accession: `GSE33630`
- platform: `GPL570`
- sample count: 105
- sample metadata rows: 105
- PTC samples: 49
- normal/control samples: 45
- ATC excluded samples: 11
- ambiguous samples: 0
- comparison candidate: PTC vs normal/control
- preflight runnable: no
- remaining blockers: `asset:expression_matrix_missing`, `expression_matrix_values_not_parsed`

The group detection gap for `patient-matched non-tumor control` is fixed. The next technical blockers are expression matrix numeric value parsing and GPL570 probe-to-symbol mapping. DEG, enrichment, and survival remain out of scope.

## GSE33630 Metadata-Only Readiness Baseline

Current baseline:

- true Series Matrix metadata parser test: passed with a manually supplied local file.
- sample count: 105.
- PTC: 49.
- normal/control: 45.
- ATC excluded: 11.
- comparison candidate: PTC vs normal/control.

Remaining blocked capabilities:

- expression matrix numeric values parse.
- GPL570 probe-to-symbol mapping.
- true runnable DEG preflight.
- DEG runner.

Recommended next options are a Series Matrix expression values parser audit, a GPL570 annotation parser audit, or a GSE60542 metadata-only readiness test. Do not start downloads, production downloader changes, DEG, enrichment, survival, or `geo_workflow.py` changes from this baseline.

## Series Matrix Expression Parser Design

The next parser layer should inspect only the expression table statistics inside an already available Series Matrix text fixture. It should not save the complete matrix and should not run analysis.

Design:

- detect `!series_matrix_table_begin` and `!series_matrix_table_end`.
- treat the first table row as the header.
- treat the first header column as the feature/probe id column, usually `ID_REF`.
- treat subsequent header columns as matrix sample ids, expected to be GSM accessions.
- count feature rows without retaining the full numeric matrix.
- count matrix sample columns.
- check whether each data cell is numeric after stripping whitespace.
- count blank / missing cells.
- count negative numeric values.
- compare matrix sample ids against metadata sample ids from `SeriesMatrixMetadataReport`.

First report-only fields:

- feature count
- sample count
- feature id column
- matrix sample ids
- numeric value status
- missing value count
- negative value count
- sample id match status
- warnings and errors

The first implementation should return a small report only. It must not write a standardized expression matrix, run DEG, perform GPL570 probe annotation, create results, create artifacts, or modify `geo_workflow.py`.

## Series Matrix Expression Report Foundation

`parse_series_matrix_expression_report(path_or_text, metadata_sample_ids=...)` now implements the first report-only expression table parser for local Series Matrix fixtures. It accepts local text, `.txt`, and `.txt.gz` inputs that are already available locally.

The parser detects the `!series_matrix_table_begin` / `!series_matrix_table_end` block, reads the header row, treats the first column as the feature/probe id column, and treats remaining columns as GSM matrix sample ids. It reports feature count, sample count, matrix sample ids, numeric value status, missing value count, negative value count, and matrix-vs-metadata sample id match status.

The helper deliberately does not return the full expression matrix and does not write a standardized expression file. It does not run DEG, perform GPL570 probe annotation, create task results, create artifacts, write execution logs, download GEO files, change production downloader behavior, or modify `geo_workflow.py`.

## GSE33630 Expression Matrix Report Test

A manually supplied local `GSE33630_series_matrix.txt.gz` file was used for a read-only expression report test. The file is local manual test data and is not committed.

Results:

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

The expression parser now clears `expression_matrix_values_not_parsed` at the report layer. The dataset is still not a runnable DEG preflight until preflight consumes the expression report and GPL570 probe-to-symbol mapping is handled. DEG, enrichment, survival, production downloader changes, and `geo_workflow.py` changes remain out of scope.

## Series Matrix Expression Report Preflight Bridge

`build_geo_series_matrix_preflight_summary(...)` can now consume an optional `SeriesMatrixExpressionReport`.

When no expression report is supplied, metadata-only preflight keeps `expression_matrix_values_not_parsed` as a blocking error. When an expression report is supplied and it has numeric values, positive feature/sample counts, and matching matrix-vs-metadata sample ids, that blocker is removed.

The bridge blocks on expression report failures such as non-numeric values, missing feature/sample rows, or sample id mismatch. Gene/platform annotation readiness remains separate: GPL570 probe-to-symbol mapping is still not implemented by this bridge, and DEG execution remains out of scope.

## GSE33630 Expression Readiness Baseline

The controlled local-file readiness baseline for `GSE33630` is now:

- saved GEO accession metadata parser: passed.
- real Series Matrix metadata parser: passed.
- group detection: passed with PTC = 49, normal/control = 45, ATC excluded = 11.
- expression matrix report: passed.
- feature count: 54675.
- matrix sample count: 105.
- metadata sample count: 105.
- sample id match status: `match`.
- numeric value status: `numeric`.
- missing value count: 0.
- negative value count: 0.

Remaining blockers:

- GPL570 probe-to-symbol mapping.
- true runnable DEG preflight.
- DEG runner.

Recommended next step is a GPL570 annotation parser audit. Do not start GPL570 parsing, DEG, enrichment, survival, downloads, production downloader changes, or `geo_workflow.py` changes without a separate scoped task.

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

## Probe Annotation Mapping Report Foundation

`PlatformAnnotationMappingReport` and `parse_platform_annotation_mapping_report(...)` provide the first fake-fixture platform annotation readiness layer. The parser accepts local text or a local small fixture file and reports platform id, probe count, mapped probe count, unmapped probe count, duplicated symbol count, mapping success rate, acceptable status, warnings, and errors.

The first parser recognizes common probe and symbol columns such as `ID`, `ID_REF`, `Probe Set ID`, `Gene Symbol`, and `Symbol`. Empty placeholders are counted as unmapped. Multi-symbol cells are collapsed to the first symbol with a warning, and duplicate target symbols are reported as warnings.

This is not a real GPL570 parser pass yet. It does not download GPL570, query GEO, run DEG, persist a full mapping table, create task results, create artifacts, or modify `geo_workflow.py`.

## Platform Mapping Report Preflight Bridge

`build_geo_series_matrix_preflight_summary(...)` can now consume an optional `PlatformAnnotationMappingReport`. When the report is acceptable, the GEO Series Matrix preflight treats gene annotation as present and no longer emits the default probe identifier mapping warning for the placeholder probe mapping path.

If the platform mapping report is missing, preflight keeps the existing probe mapping readiness warning. If the platform mapping report is present but unacceptable, the preflight records `platform_mapping:*` blocking errors and remains non-runnable.

This bridge still does not run DEG and does not parse a real GPL570 file. It only connects fake-fixture platform mapping readiness into preflight so the next controlled step can test a manually supplied GPL570 annotation fixture under a separate scope.

## GPL570 Annotation Readiness Manual-Test Plan

A future controlled manual test should use a locally supplied GPL570 annotation file and keep that file out of git. The test should record the detected probe id column, gene symbol column, probe count, mapped probe count, unmapped probe count, duplicated symbol count, mapping success rate, acceptable status, warnings, and errors.

The manual test should decide whether the platform mapping report is acceptable enough to clear the GSE33630 probe-to-symbol readiness blocker. It must not download GPL570, run DEG, create results, create artifacts, change production downloader behavior, or modify `geo_workflow.py`.

## v0.35 GPL570 Mapping Readiness Baseline

`v0.35-gpl570-mapping-readiness` marks the first GPL570 mapping readiness foundation. It includes the GPL570 annotation parser design audit, `PlatformAnnotationMappingReport`, fake/local fixture parsing through `parse_platform_annotation_mapping_report(...)`, a preflight bridge that can consume acceptable platform mapping reports, and a GSE33630 manual-test template for a future locally supplied GPL570 annotation file.

Still not implemented:

- real GPL570 download.
- real GPL570 manual file test.
- DEG runner.
- enrichment or survival.
- production downloader changes.
- `geo_workflow.py` changes.

Recommended next step: manually provide a GPL570 annotation file for controlled readiness testing, or audit the exact real GPL570 file format before parser hardening.

## GPL570 Manual File First Parser Check

A locally supplied GPL570 annotation file was checked read-only at `/Users/changdali/Documents/model9-main-clean/tests/geodatabase/GPL570-55999 (1).txt`. The file is manual test data and remains untracked.

Current parser result:

- probe count: 0.
- mapped probe count: 0.
- mapping success rate: 0.0.
- acceptable: no.
- errors: `probe_id_column_missing`, `gene_symbol_column_missing`.

Manual inspection shows the real tabular header starts after leading comment metadata: line 17 begins with `ID` and includes `Gene Symbol`. The current parser expects the header on the first line, so the next parser-hardening task should skip leading comment lines and detect the first valid table header.

No real DEG, enrichment, survival, production downloader changes, committed GEO files, or `geo_workflow.py` changes were performed.

## GPL Annotation Header Detection Hardening

`parse_platform_annotation_mapping_report(...)` now searches for the first real table header after optional leading metadata/comment lines. This supports GPL570-style files where comment rows start with `#` and the tabular header appears later, for example with `ID` and `Gene Symbol` columns.

If no header row contains both a supported probe id column and a supported gene symbol column, the parser returns the stable error `platform_annotation_header_missing`. This remains parser/readiness only: no GPL download, DEG, enrichment, survival, production downloader change, or `geo_workflow.py` change is included.

## GPL570 Annotation Parser Retest

The hardened platform annotation parser was retested against the local manual GPL570 annotation file. Results:

- file size: 79501274 bytes.
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

The GPL570 probe-to-symbol mapping blocker is cleared at mapping-report level. The local GPL570 file remains untracked. No DEG, enrichment, survival, production downloader change, or `geo_workflow.py` change was performed.

## GSE33630 Preflight After GPL570 Mapping

Combining the local GSE33630 Series Matrix metadata report, expression report, group detection report, and GPL570 mapping report yields a runnable readiness/preflight summary:

- `expression_matrix_values_not_parsed`: cleared.
- GPL570 probe-to-symbol mapping: cleared.
- feature count: 54675.
- sample count: 105.
- sample mapping match rate: 1.0.
- mapping success rate: 0.8373.
- PTC samples: 49.
- normal/control samples: 45.
- ATC excluded samples: 11.
- preflight runnable: yes.
- remaining blockers: none.

This is readiness/preflight only. DEG, enrichment, survival, production downloader changes, and `geo_workflow.py` changes remain out of scope.

## GSE33630 DEG Runner Readiness Decision

GSE33630 is now ready for a DEG runner design audit based on readiness evidence only:

- expression values are report-checked and numeric.
- sample mapping is complete.
- group detection identifies PTC vs normal/control and excludes ATC.
- GPL570 mapping is acceptable.
- readiness/preflight has no blocking errors.

This is not DEG execution. It only authorizes a future design audit. Do not implement limma, DESeq2, edgeR, enrichment, survival, production downloader changes, or `geo_workflow.py` changes from this decision.

## GSE33630 DEG Runner Design Audit

`docs/geo_deg_runner_design.md` records the first DEG runner design audit. The recommended next implementation is a DEG-ready matrix builder, not formal DEG statistics, because the current runtime dependencies do not include a statistical stack such as scipy or statsmodels.

The design keeps the first scope narrow: GSE33630-like Series Matrix input, two-group PTC vs normal/control comparison, local files only, GPL570 mapping readiness, and explicit probe-to-symbol collapse reporting. It excludes enrichment, survival, batch correction, multi-group analysis, production downloader changes, and `geo_workflow.py` changes.

## v0.36 GSE33630 DEG Readiness Baseline

`v0.36-gse33630-deg-readiness` records the first GSE33630 DEG readiness baseline. The controlled readiness evidence now has:

- GSE33630 preflight runnable: yes.
- GPL570 probe-to-symbol mapping acceptable: yes.
- expression report: 54675 features, 105 samples, numeric values, matched sample ids.
- group detection: 49 PTC, 45 normal/control, 11 ATC excluded.
- DEG-ready matrix builder foundation: `DegReadyMatrixReport` and `build_deg_ready_matrix_report(...)`.

The DEG-ready matrix builder is a readiness/reporting foundation only. It uses fake/small fixtures, records mean collapse strategy for duplicated gene symbols, and does not run formal statistical tests.

Still not implemented:

- formal DEG statistics.
- limma, DESeq2, or edgeR.
- enrichment analysis.
- production downloader changes.
- `geo_workflow.py` changes.

Next recommended work is either a real GSE33630 DEG-ready matrix manual test using local untracked files, or a separate minimal two-group DEG statistical runner audit.

## GSE33630 DEG-Ready Matrix Manual Test Scope

The controlled manual test should use only local untracked files:

- `tests/geodatabase/GSE33630_series_matrix.txt.gz`
- `tests/geodatabase/GPL570-55999 (1).txt`

The test objective is a DEG-ready matrix readiness report that verifies probe-to-symbol mapping application, duplicated gene-symbol collapse readiness, and PTC vs normal/control grouping. Expected sample groups remain PTC = 49 and normal/control = 45.

The report should include feature count, mapped feature count, unmapped feature count, duplicated gene count, gene count after collapse, case count, control count, collapse strategy, ready yes/no, warnings, and errors.

This scope explicitly excludes formal DEG statistics, p-values, formal logFC, enrichment, a DEG result table, production downloader changes, committed local GEO/GPL files, and `geo_workflow.py` changes.

## GSE33630 DEG-Ready Matrix Manual Report

The local untracked GSE33630 Series Matrix and GPL570 annotation files produced a read-only DEG-ready matrix report:

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

This clears the DEG-ready matrix readiness step. Remaining work is a separate minimal two-group DEG statistical runner audit. Formal DEG statistics, p-values, formal logFC, enrichment, production downloader changes, committed GEO/GPL files, and `geo_workflow.py` changes remain out of scope.

## GSE33630 DEG-Ready Matrix Baseline

The controlled GSE33630 path now connects expression matrix readiness, sample grouping, and GPL570 mapping into the DEG-ready matrix report. The report is ready with 54675 features, 45782 mapped features, 8893 unmapped features, 22880 genes after mean collapse, 105 samples, 49 cases, and 45 controls.

The baseline remains pre-statistical. It does not produce p-values, formal logFC, limma/DESeq2/edgeR output, enrichment results, production downloader changes, committed GEO/GPL files, or `geo_workflow.py` changes.

Next recommended step: minimal two-group DEG statistical runner audit.

## GEO Family SOFT Parser

The readiness harness supports a local-file GEO family SOFT path for datasets where the available manual input is `family.soft` or `family.soft.gz` rather than a Series Matrix file.

The metadata parser extracts:

- `^SERIES` / `!Series_geo_accession`
- `!Series_platform_id`
- `!Series_sample_id`
- per-sample `^SAMPLE`
- `!Sample_geo_accession`
- `!Sample_title`
- `!Sample_source_name_ch1`
- `!Sample_characteristics_ch1`
- `!Sample_platform_id`

The expression report parser reads per-sample `!sample_table_begin` / `!sample_table_end` sections and reports only readiness statistics:

- feature count
- sample count
- feature id column
- matrix sample ids
- numeric value status
- missing value count
- negative value count
- sample id match status

The platform mapping parser can read an embedded SOFT `!platform_table_begin` / `!platform_table_end` section and produce a `PlatformAnnotationMappingReport` without writing a mapping artifact.

The SOFT path does not return the full expression matrix, does not write a matrix artifact, does not download GEO files, does not run DEG, and does not modify `geo_workflow.py`.

The local harness accepts the input with:

```bash
python3 scripts/run_real_geo_readiness_test.py \
  --dataset-id GSE27155 \
  --soft-file <family.soft.gz> \
  --json
```

The first `GSE27155` SOFT inspection exposed a group-detection issue from real metadata: non-PTC samples can include a field name such as `morphology of papillary carcinomas: NA`. That field name alone must not classify the sample as PTC. Group detection now evaluates `characteristics_ch1` key/value fragments so `NA` morphology values do not become PTC evidence, while actual PTC labels in title/source fields and meaningful morphology values remain detectable.

For the default PTC-vs-normal readiness candidate, follicular thyroid carcinoma/adenoma, oncocytic thyroid carcinoma/adenoma, medullary thyroid carcinoma, anaplastic thyroid carcinoma, LNM, and recurrence labels are treated as excluded non-target groups rather than as ambiguous PTC/normal samples. This does not create a final comparison automatically; it only keeps the PTC-vs-normal candidate from being polluted by known non-target classes.

## GSE27155 SOFT Readiness Result

Using the local untracked `GSE27155_family.soft.gz` file, the SOFT parser produced a readiness result:

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
- preflight runnable: true.

Remaining blockers:

- Multi-class comparison policy still requires manual confirmation before any formal analysis.

This result confirms that GSE27155 is usable as a multi-class group-filtering, SOFT expression-readiness, and GPL96 mapping-readiness benchmark. The PTC-vs-normal/control comparison is a readiness candidate, but the normal/control arm has only 4 samples. Reports should show a small-control warning for this dataset, and it should not be used as the primary formal DEG demonstration benchmark.

It is not a formal DEG-ready baseline until comparison policy, small-control warning behavior, and downstream DEG scope are handled in separate scoped tasks.

## Minimal Two-Group DEG Runner Design

The next runner design should consume DEG-ready GSE33630-like inputs only: the DEG-ready matrix report or future gene-level matrix, sample group labels, and the fixed PTC vs normal/control comparison.

Because the current runtime dependency set does not include scipy or statsmodels, a first implementation can stay standard-library-only and produce effect-size summaries rather than formal hypothesis tests. Acceptable first outputs are `DegResultSummary` and an effect-size-only `deg_result_table.csv` with case mean, control mean, mean difference, and log2FC summary. This table must clearly omit p-values and FDR-adjusted p-values.

Formal p-values, FDR, volcano-ready tables, t-tests, and multiple-testing correction should wait for a separate statistical dependency audit. The runner design continues to exclude limma, DESeq2, edgeR, enrichment, survival, batch correction, production downloader changes, and `geo_workflow.py` changes.
