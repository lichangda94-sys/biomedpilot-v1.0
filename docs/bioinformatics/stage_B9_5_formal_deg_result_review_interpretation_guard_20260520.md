# Bioinformatics B9.5 Formal DEG Result Review and Basic Interpretation Guard

Date: 2026-05-20

## Scope

B9.5 adds a review-only surface for audited formal DEG results. It does not generate plots, reports, GSEA, survival analysis, or clinical advice.

The review accepts only result index v2 entries where:

- `task_type=deg`
- `result_semantics=formal_computed_result`
- output artifact includes `artifact_type=deg_result_table`

Imported, testing, exploratory, preflight, blocked, and failed results are excluded from formal DEG review.

## Review Surface

Formal DEG review displays:

- `feature_id`
- `gene_symbol`
- `log2_fold_change`
- `p_value`
- `adjusted_p_value`
- `significance_label`

Summary includes:

- total gene count
- significant up/down counts
- thresholds
- method
- dependency versions
- case/control sample counts

Guard copy:

> Formal DEG review shows statistical analysis results only. It is not a clinical conclusion or treatment recommendation.

## Sorting And Filtering

Supported sorting:

- FDR / `adjusted_p_value`
- p-value
- log2FC
- significance label
- input order

Supported filters:

- all
- significant
- up
- down
- not significant

## Export Boundary

Export supports only reviewed DEG table copies:

- TSV
- CSV

Export does not create a report-ready package and returns:

- `report_ready_eligible=False`
- `plot_artifacts=[]`
- `report_artifacts=[]`

## Provenance Panel

The provenance panel shows:

- input package id
- parameter confirmation path
- dependency snapshot presence
- task-run log artifact
- result table path
- result index path
- plot/report artifact status
- report-ready eligibility

## Disabled Downstream

B9.5 explicitly displays downstream boundaries:

- plot: waiting for B9.6 plot artifact gate; no volcano or heatmap is generated
- report-ready: waiting for B9.7 report-ready gate
- GSEA: not entered from B9.5
- survival: not entered from B9.5

## Validation

Passed checks:

```bash
git diff --check
python3 -m pytest tests/bioinformatics/test_formal_deg_result_review.py -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "results_browser"
python3 -m pytest tests/bioinformatics -q -k "formal_deg_result_review or formal_controlled_deg or parameter_confirmation"
python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
python3 -m app.main --smoke-test
python3 scripts/package_app.py --smoke-test
open -W -n dist/BioMedPilot.app --args --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```

Observed totals:

- formal DEG result review service tests: 3 passed
- results browser UI tests: 2 passed
- focused formal DEG/confirmation review tests: 10 passed
- full bioinformatics suite: 363 passed
- full UI suite: 175 passed
- controlled scipy/statsmodels runtime check: passed, arm64, p-value/FDR present, plot/report empty, report-ready false

## Conclusion

B9.5 implements formal DEG review and basic interpretation guard while preserving downstream boundaries. The next stage can address B9.6 plot artifact gate without treating this review table as a plot or report-ready output.
