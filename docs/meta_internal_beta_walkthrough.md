# Meta Internal Beta Walkthrough

Current status: Developer Preview / testing. Do not use generated outputs as production clinical or statistical conclusions.

## Sample Projects

Use committed source inputs only. Create generated project outputs in a temporary project directory.

### Treatment Effect Binary OR

- Directory: `examples/meta_analysis_internal_beta_samples/treatment_effect_binary_or`
- Input: `inputs/literature.csv`
- Expected import count: 3
- Expected duplicate count: 1
- Expected screening status: 2 included, 0 excluded, 0 maybe
- Expected extraction: binary `Clinical response`, effect measure `OR`, two manually seeded studies
- Expected analysis: random model testing run with pooled OR direction greater than 1 in seeded data

### Biomarker Prevalence / Correlation

- Directory: `examples/meta_analysis_internal_beta_samples/biomarker_prevalence_correlation`
- Input: `inputs/literature.csv`
- Expected import count: 3
- Expected duplicate count: 0
- Expected screening status: 3 included, 0 excluded, 0 maybe
- Expected extraction: proportion `Marker positive` and correlation with clinical score
- Expected analysis: prevalence uses logit transformed proportion; correlation uses Fisher z transform; small-study warnings are expected

## Walkthrough Steps

1. Create a temporary Meta project directory.
2. Import the sample CSV through the Literature Import workflow.
3. Review import diagnostics and recent import batches.
4. Review duplicate candidates and merge preview. Do not auto-merge without reviewer confirmation.
5. Apply title/abstract screening decisions according to the expected manifest.
6. Mark full-text status manually. Do not use automatic PDF download, OCR, or institutional access.
7. Seed or enter extraction values from the expected manifest.
8. Complete quality assessment with the recommended testing tool.
9. Build an analysis-ready dataset and run the testing analysis.
10. Generate forest/funnel outputs only inside the temporary project.
11. Generate simplified PRISMA, formal Markdown/HTML/DOCX testing report, supplementary exports, and reproducibility package.
12. Compare generated artifacts against the sample expected manifest and record any blocker or major warning.

## Expected Warnings

- Developer Preview / testing status.
- Manually seeded extraction values.
- Small-study warnings for publication bias, funnel plot, and random effects where applicable.
- Missing formal PDF export.
- Simplified PRISMA SVG is not formal PRISMA 2020.
