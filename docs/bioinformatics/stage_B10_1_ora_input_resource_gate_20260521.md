# Bioinformatics B10.1 ORA Input / Resource / Parameter / Result Schema Gate

Date: 2026-05-21

## Scope

B10.1 implements gate-only preparation for future controlled ORA/pathway enrichment. It adds ORA readiness contracts for:

- source result input eligibility;
- local gene set resource validation;
- ORA parameter manifest validation;
- future ORA result index v2 schema validation;
- Analysis Center gate rows and disabled action reasons.

This stage does not execute ORA, does not generate enrichment result tables, does not generate pathway plots, does not enter report-ready, and does not activate GSEA, survival, or clinical statistics.

## Existing Enrichment Audit

`app/bioinformatics/services/enrichment_runner.py` is an older execution runner. It reads a DEG CSV plus GMT resource and writes enrichment outputs (`enrichment_results.csv`, `enrichment_summary.json`) with `enrichment_executed=True`. B10.1 did not migrate or activate this runner because this stage is explicitly gate-only.

`app/bioinformatics/gene_set_resources.py` already provides local GMT validation and a project registry. B10.1 reuses local validation/registry metadata only. It does not call online Reactome/GO/KEGG download paths.

No legacy, Integration, archive, or ReleaseBuild handoff logic was copied into formal ORA execution.

## ORA Input Gate

New module: `app/bioinformatics/enrichment/input_gate.py`

Allowed source inputs:

- formal DEG result with `result_semantics=formal_computed_result`, `task_type=deg`, valid result index v2, DEG table artifact, and `adjusted_p_value`;
- imported DEG result with `result_semantics=imported_external_result`, explicit external provenance, confirmed column mapping, DEG-like gene/log2FC/FDR/significance fields.

Blocked source inputs:

- raw expression matrices;
- TPM/FPKM/count matrices before DEG result creation;
- `testing_level`, `exploratory`, `preflight_only`, `configured_not_run` / dry-run outputs;
- non-DEG task results;
- plot artifacts or report packages alone.

The produced ORA input package includes `ora_input_id`, source result semantics, source result index path, DEG table path, gene ID type, selected gene/background policies, selected/background counts, warnings, blockers, and provenance.

## Gene Set Resource Gate

New module: `app/bioinformatics/enrichment/gene_set_gate.py`

Supported resources:

- direct local GMT file;
- project gene set registry entries.

Blocked conditions:

- missing resource or missing file;
- malformed GMT;
- empty terms or empty genes;
- known species mismatch;
- known gene ID mismatch without mapping;
- MSigDB-like resource missing manual source/license evidence.

No online download is performed in this gate.

## Parameter Gate

New module: `app/bioinformatics/enrichment/parameter_gate.py`

The ORA parameter manifest includes:

- `ora_parameter_id`;
- `ora_input_id`;
- `gene_set_resource_id`;
- source result id and semantics;
- selected gene and background universe rules;
- min/max gene set size;
- p-value and FDR thresholds;
- multiple-testing policy;
- test method (`hypergeometric` or `fisher_exact`);
- gene ID and species policies;
- warnings and blockers.

Blocked conditions include missing source result, non-DEG source, non-formal/non-imported semantics, failed ORA input gate, missing gene set, invalid thresholds, missing multiple testing policy, empty selected genes/background universe, unsupported test method, invalid gene set size bounds, and unresolved gene ID mismatch.

## Result Schema Gate

New module: `app/bioinformatics/enrichment/result_schema.py`

This defines the future `ora_enrichment` result index v2 contract and validates candidate entry/table shape only. Required future table columns are:

- `term_id`
- `term_name`
- `gene_set_size`
- `overlap_count`
- `overlap_genes`
- `background_size`
- `selected_gene_count`
- `p_value`
- `adjusted_p_value`
- `enrichment_ratio`
- `source_gene_list`
- `warnings`

B10.1 keeps `report_ready_eligible=False`, forbids ORA report-ready integration, and does not register ORA results.

## UI Gate Changes

Updated modules:

- `app/bioinformatics/analysis_ui/state.py`
- `app/bioinformatics/analysis_ui/action_rules.py`
- `app/bioinformatics/workflow_pages.py`

Analysis Center now exposes `ora_gate_rows` for:

- ORA source DEG result;
- ORA gene set resource;
- ORA parameter manifest;
- ORA future result schema;
- B10.2 controlled ORA execution blocker.

Action matrix changes:

- `ora_readiness_review` can be shown for gate review/configuration only;
- `run_ora_enrichment` is always disabled with `b10_2_controlled_ora_execution_required`;
- `ora_plot` is disabled/hidden;
- `ora_report_ready` is disabled/hidden;
- formal GSEA remains disabled/hidden.

UI copy was updated to state that ORA readiness is contract-driven and that preflight/testing/imported outputs are not upgraded to formal results.

## Configuration

`config/bioinformatics/enrichment_defaults.yaml` now records the B10.1 ORA gate policy:

- allowed sources: formal DEG and imported DEG;
- forbidden sources: raw expression, preflight, testing, exploratory, dry-run;
- resources: local GMT/project registry only;
- online download: false;
- future methods: hypergeometric, fisher_exact;
- report-ready: false.

## Tests

Commands run:

- `git diff --check` - passed
- `python3 -m pytest tests/bioinformatics/test_ora_input_gate.py tests/bioinformatics/test_ora_gene_set_gate.py tests/bioinformatics/test_ora_parameter_gate.py tests/bioinformatics/test_ora_result_schema_gate.py -q` - 18 passed
- `python3 -m pytest tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_ui_action_rules.py -q` - 12 passed
- `python3 -m pytest tests/bioinformatics -q -k "formal_deg or result_semantics or enrichment or ora or analysis_ui"` - 61 passed, 378 deselected
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or results_browser or report"` - 13 passed, 96 deselected
- `python3 -m pytest tests/bioinformatics -q` - 439 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` - 266 passed
- `python3 -m app.main --smoke-test` - passed

Package smoke, `open -W`, and `codesign` were not rerun because B10.1 did not modify package scripts, app launcher, dependency packaging, or bundle metadata.

## Blockers / Major / Minor

Blockers: none for B10.1 gate-only scope.

Major issues: none.

Minor issues:

- ORA has no execution backend in B10.1 by design.
- ORA UI currently provides readiness rows and disabled reasons, not a full parameter editor.
- MSigDB support requires user-provided local GMT and license/source confirmation.

## Boundaries Preserved

- No formal ORA execution.
- No enrichment p-values or adjusted p-values are generated.
- No ORA plot artifact.
- No ORA report-ready package section.
- No GSEA activation.
- No survival/KM/Cox/log-rank/HR activation.
- No clinical conclusion.
- No raw expression bypass into ORA.
- No online pathway database auto-download.

## Next Step

Proceed to B10.2 controlled ORA execution/result review only after accepting these gates. B10.2 should remain limited to controlled ORA MVP execution from eligible DEG result plus validated local gene set resource.
