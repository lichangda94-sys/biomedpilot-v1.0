# Real Dataset Fixture Regression Policy

Real dataset testing should improve parser and readiness reliability without committing full GEO/GPL files.

## Rule

When a controlled real dataset exposes a failure mode, create a minimal fixture that isolates the failure. Do not commit full Series Matrix files, RAW archives, supplementary datasets, platform annotation dumps, or user-provided private files.

## Fixture Requirements

Each committed fixture must:

- be a small text snippet.
- contain only the minimum lines needed to reproduce the failure.
- have a clear test purpose.
- map to one gap category from the real dataset test harness.
- be covered by a unit test.

## Recommended Fixture Locations

```text
tests/fixtures/geo/
  gse33630_non_tumor_control_samples.txt
  gpl570_header_after_hash_metadata.txt
  series_matrix_characteristics_ch1_multiline.txt
```

## Gap To Fixture Workflow

1. Run `scripts/run_real_geo_readiness_test.py` on local manual inputs.
2. Review `readiness_report.json` / `readiness_report.md`.
3. Identify the gap category and source.
4. Extract the smallest non-sensitive snippet that reproduces the problem.
5. Add a unit test that fails before the parser/readiness fix.
6. Fix parser, mapping, group detection, readiness, or UI warning logic.
7. Rerun full tests.
8. Update the dataset registry status.

## Gap Category Mapping

Use the gap category to choose the fixture type and target test:

| gap category | fixture type | target test area |
| --- | --- | --- |
| `metadata_parse_gap` | saved GEO HTML/text snippet | accession metadata parser |
| `series_matrix_parse_gap` | Series Matrix metadata/table snippet | Series Matrix parser |
| `group_detection_gap` | sample title/source/characteristics snippet | group detection |
| `platform_mapping_gap` | platform annotation header/row snippet | platform annotation parser |
| `sample_mapping_gap` | matrix header plus sample metadata snippet | sample mapping readiness |
| `comparison_readiness_gap` | sample metadata and expected group rule snippet | comparison readiness/preflight |

Fixture names should follow:

```text
tests/fixtures/geo/<dataset>_<gap_type>_<short_desc>.txt
```

Examples:

```text
tests/fixtures/geo/gse60542_group_detection_nodal_metastasis.txt
tests/fixtures/geo/gse27155_platform_mapping_multiclass_annotation.txt
tests/fixtures/geo/gse33630_series_matrix_non_tumor_control.txt
```

Fixtures should generally stay under 200 lines and under 25 KB unless a parser boundary requires a larger minimal sample. Any larger fixture needs an explicit reason in the test docstring or adjacent README.

Every committed fixture must record:

- source dataset id.
- gap category.
- original failure summary.
- intended parser/readiness behavior.
- owning unit test.

Do not commit a fixture without a corresponding test. If the failure cannot be reduced safely, keep the full file local and document the gap in the registry instead.

The next possible implementation is a fixture scaffold generator that creates the filename, metadata header, and empty test stub from a `RealDatasetGap`. This task only audits that workflow and does not implement the generator.

## Examples

| gap category | real failure pattern | fixture purpose |
| --- | --- | --- |
| `metadata_parse_gap` | GEO HTML sample count stored in an unexpected table label | ensure accession parser extracts sample count |
| `group_detection_gap` | `patient-matched non-tumor control` not recognized | ensure normal/control detection covers non-tumor wording |
| `gene_mapping_gap` | GPL570 header appears after `#` metadata rows | ensure platform parser finds delayed tabular header |
| `series_matrix_parse_gap` | multiple `!Sample_characteristics_ch1` rows | ensure Series Matrix metadata rows preserve combined characteristics |

## Non-Goals

- no full real data file commits.
- no production downloader changes.
- no GEO/GPL downloads.
- no DEG/enrichment/survival execution.
- no `geo_workflow.py` changes.

## v0.40 Harness Fixture Boundary

The Real Dataset Test Harness MVP records gaps through `RealDatasetGap`, but it does not commit generated harness reports or local real data files. `real_dataset_tests/`, full Series Matrix files, full GPL annotation files, RAW archives, and supplementary files remain local-only.

For the v0.40 GSE33630 smoke, no regression fixture is required because the harness report has `gap_count=0`. Future GSE60542/GSE27155 failures should be converted into small fixtures only when a specific parser/readiness gap is identified.
