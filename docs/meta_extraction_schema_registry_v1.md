# Meta Data Extraction Schema Registry v1

Stage M12 adds a typed extraction schema registry for Meta Analysis projects.

## Active Service

- Service: `app/meta_analysis/services/extraction_schema_registry_v1_service.py`
- Registry artifact: `extraction/schema_registry_v1.json`
- Selected schema artifact: `extraction/selected_extraction_schema_v1.json`

## Covered Meta Types

- Binary outcome Meta: OR / RR / RD
- Continuous outcome Meta: MD / SMD / WMD
- Survival outcome Meta: HR / 95% CI
- Prevalence / incidence Meta
- Diagnostic accuracy Meta: TP / FP / FN / TN
- Exposure-disease risk Meta: OR / RR / HR
- Biomarker expression difference Meta: mean / SD / n
- Correlation Meta: r / Fisher z
- Prognostic factor Meta: HR / OR
- Dose-response Meta: dose / cases / non-cases / person-years

## Schema Contents

Each schema stores:

- required fields
- optional fields
- validation rules
- effect-size mapping
- analysis defaults
- quality-tool recommendation
- report-template mapping

## Governance

- Saving the registry is a draft engineering artifact.
- Selecting a schema can be draft or reviewer-confirmed.
- Schema selection does not write final extraction data.
- Schema selection does not create analysis-ready datasets or PRISMA counts.

## Current Limitations

- The registry provides form templates and validation contracts only.
- Manual extraction UI v1 is the next stage.
- AI/model extraction suggestions remain future queue work and must not overwrite final extraction values.
