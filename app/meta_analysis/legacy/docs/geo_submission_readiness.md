# GEO Submission Readiness Design

This audit defines the minimum manual GEO submission readiness checks for standardized local datasets. It is documentation only. It does not submit data, upload files, contact GEO, download public data, parse raw sequencing files, or change `geo_workflow.py`.

## Purpose

The checker should answer whether a standardized local package is likely ready for manual GEO submission review. It is not an automated submission system and does not make privacy or compliance decisions on behalf of the user.

## Required Readiness Signals

The first report should capture:

- processed expression matrix presence.
- sample metadata presence.
- sample id consistency between expression matrix and metadata.
- gene annotation presence.
- raw FASTQ availability as a warning-level signal.
- sample-to-raw-file mapping availability.
- reference genome information.
- annotation version information.
- processing software information.
- human-subject privacy warning.

## Readiness Levels

- `insufficient`: required processed expression or sample metadata is missing, or samples do not align.
- `partial`: core processed files exist, but important submission metadata is incomplete.
- `likely_ready_for_manual_geo_submission`: processed data and required metadata are present enough for manual review.

The readiness level is a review signal only. It should not upload data, block workflows, or imply that a submission will be accepted.

## Boundary

The checker should not:

- submit to GEO.
- create a production uploader.
- upload user data.
- delete, move, or overwrite raw files.
- parse FASTQ/BAM/CRAM contents.
- run FastQC/MultiQC.
- run alignment or quantification.
- run DEG/enrichment analysis.
- change `geo_workflow.py`.

## Recommended First Implementation

The first implementation should consume a standardized local dataset manifest plus selected metadata fields. It should produce a `GeoSubmissionReadinessReport` with warnings and errors, using fake/temp fixtures in tests.

## GEO Submission Readiness Checker

`build_geo_submission_readiness_report(...)` creates a read-only `GeoSubmissionReadinessReport` for manual GEO submission review. It records:

- raw FASTQ availability.
- processed count matrix availability.
- normalized expression matrix availability.
- sample metadata availability.
- gene annotation availability.
- sample-to-raw-file mapping availability.
- reference genome information availability.
- annotation version information availability.
- processing software information availability.
- human subject privacy warning status.
- readiness level.
- warnings and errors.

Readiness levels are:

- `insufficient`: required processed expression data or sample metadata is missing, or expression samples and metadata samples do not match.
- `partial`: core processed data is present, but FASTQ, mapping, reference, annotation, software, or privacy review information still needs manual review.
- `likely_ready_for_manual_geo_submission`: processed expression data, sample metadata, sample alignment, raw-file mapping, gene annotation, reference, annotation version, and processing software information are present.

The checker does not contact GEO, submit data, upload files, parse raw reads, run analysis, or mutate local assets.

## v0.33 Baseline Boundary

The GEO submission readiness checker is included in `v0.33-local-dataset-standardization`. It is a manual-readiness signal for local standardized packages only. It does not automate GEO submission, upload user files, contact external services, parse FASTQ/BAM/CRAM contents, or change production downloader behavior.
