# B83 Controlled R Enrichment Adapter

## Scope

B83 adds controlled Rscript execution adapters for the enrichment capabilities already available in the current external R environment. It builds on B81 resource gates and B82 backend capability gates.

This stage is limited to:

- controlled ORA through `clusterProfiler::enricher`;
- controlled preranked GSEA through `fgsea`;
- result index v2 registration;
- parameter manifest and task-run log capture;
- graceful blocking when the R backend gate or Rscript execution fails.

## Implemented

Added `app/bioinformatics/enrichment_r_adapter.py`:

- `run_controlled_ora_r_fixture(...)`
- `run_controlled_gsea_preranked_r_fixture(...)`

Both functions:

- consume `build_enrichment_backend_gate(...)`;
- require selected capability gates to pass;
- call external `Rscript` detect-first;
- write controlled TSV outputs under `results/tables/`;
- write parameter manifests under `manifests/enrichment/`;
- write task logs under `analysis/enrichment/`;
- register result index v2 entries with `result_semantics=formal_computed_result` only after all gates and output validation pass;
- keep `plot_artifacts=[]`;
- keep `report_artifacts=[]`;
- keep `report_ready_eligible=False`.

## Current Capability Decisions

Activated for controlled fixtures:

- `clusterProfiler::enricher` ORA using controlled TERM2GENE / TERM2NAME input.
- `fgsea` preranked GSEA using controlled ranked stats and pathway input.

Still not activated:

- ReactomePA pathway ORA.
- msigdbr catalog driven resources.
- enrichment map / pathway diagrams.
- report-ready enrichment sections.
- full integrated report upgrades.
- clinical interpretation.

## Boundaries

- No automatic R package installation.
- No network download.
- No package bundling into `.app`.
- No fallback statistics when Rscript fails.
- No ReactomePA or msigdbr workaround.
- No GSEA/ORA UI formal run button change in this stage.

## Validation

Focused tests cover:

- ORA adapter registering a formal result index v2 entry only after the backend gate and output validation pass;
- GSEA adapter registering a formal result index v2 entry only after the backend gate and output validation pass;
- missing detection payload blocking without traceback;
- Rscript failure blocking without writing result index entries;
- plot/report artifacts and report-ready eligibility staying disabled.

Real local smoke was also run against the external detector payload from ReleaseBuild:

- ORA: passed.
- GSEA: passed.
- result index written in a temporary project.
