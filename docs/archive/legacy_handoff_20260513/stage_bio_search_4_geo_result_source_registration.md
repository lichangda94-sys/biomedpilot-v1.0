# Stage Bio-Search-4 GEO Result Source Registration

## Summary

GEO/GSE search candidates can be registered as project data sources from the
Bioinformatics Chinese dataset search page. Registration is a planning handoff
only: it does not download GEO files, run data recognition, or declare the
dataset analysis-ready.

## Registered Source Record

GEO candidates are written as acquisition records with:

- `source_type = geo_accession`
- `accession`
- `title`
- `organism`
- `sample_count`
- `platform_accessions`
- `geo_url`
- `query_used`
- `search_time`
- `source_database = NCBI GEO`
- `download_plan_available`
- `ready_for_recognition = pending`

The metadata audit block records `event_type = geo_source_registered`,
`accession`, `query_used`, `registered_at`, and `user_action`.

## Guardrails

- A project must be open before registration.
- Duplicate GSE registration in the same project is not repeated.
- Registration remains `plan_only`; raw data download and analysis are separate
  later workflow stages.
