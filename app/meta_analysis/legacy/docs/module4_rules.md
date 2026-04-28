# Module 4 Rules And Profiles

Module 4A provides the extraction quality rule foundation. The current `RuleService` lives under `extraction/` and performs lightweight rule checks against `ExtractionRecord` and `OutcomeRecord` objects.

This layer checks whether extracted records look valid enough for review. It does not block pipelines or replace later analysis configuration work.

## Module 4A Current Scope

Extraction rule support:

- rule definition
- rule persistence through JSON store
- evaluation result persistence
- create rule
- update rule
- list rules
- evaluate `ExtractionRecord`
- evaluate `OutcomeRecord`
- required field check
- numeric range check
- allowed values check
- `passed` / `failed` / `skipped` results
- severity and enabled flags

Persisted files:

- `extraction/extraction_rules.json`
- `extraction/rule_evaluation_results.json`

## Module 4B Current Scope

Analysis profile support:

- `GenePanel`
- `ComparisonRule`
- `KeywordRuleSet`
- `ThresholdProfile`
- `AnalysisProfile`
- `AnalysisProfileService`
- validation for cross-project references and metric/outcome compatibility
- `EngineReadyAnalysisConfig` export for downstream analysis consumption

Module 4B provides profile structure and export. Module 5 consumes exported profile configs, and Module 6 can surface profile source metadata in reporting summaries.

## Out Of Scope

Currently not included:

- no `geo_workflow.py` changes
- no automatic `ExtractionService` blocking
- no workflow blocking
- no complex nested condition engine
- no production validation policy engine
- no production TCGA/GDC/GTEx downloader
- no real-data dependency
- no complex UI workflow
- no Module 7 task orchestration yet

Failed rule evaluations are recorded as data. They do not automatically stop import, screening, extraction, analysis, reporting, or any later workflow.

## Module 4A Versus Module 4B

Module 4A:

- extraction quality rule service
- checks whether extracted records look valid
- works on `ExtractionRecord` / `OutcomeRecord`
- produces evaluation results

Module 4B:

- analysis configuration rules
- gene panels
- comparison definitions
- keyword sets
- threshold profiles
- analysis profiles
- engine-ready config export for Module 5 / Module 6

## Example Flow

Pseudo-code only:

```python
service = RuleService.from_root_dir(workspace_root)

rule = service.create_rule(
    project_id="proj-demo",
    target_type=RuleTargetType.EXTRACTION_RECORD,
    check_type=RuleCheckType.REQUIRED_FIELD,
    field_name="study_design",
)

results = service.evaluate_extraction_record("extr-demo")

for result in results:
    print(result.status, result.message)
```

The evaluation result is persisted through the JSON rule store and can be inspected later.

## Consumer Diagnostics

Rule bundle diagnostics can now be surfaced through repo smoke/check reporting as a consumer-facing summary. This remains reporting-only and does not block `ExtractionService` or `geo_workflow.py`.
