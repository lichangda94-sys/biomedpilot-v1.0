# Shared Medical Vocabulary: Meta Analysis Terms Core v1

## Scope

Meta Analysis Terms Core v1 adds curated terminology for Chinese research-question understanding, PICO/PICOS/PECO decomposition, PubMed and MeSH query drafting, publication-type filtering, effect measure recognition, outcome recognition, diagnostic accuracy terms, heterogeneity terms, and quality assessment tools.

This stage only handles shared vocabulary. It does not change Bioinformatics recognition, Bioinformatics UI, Meta UI, or workflow adapters.

## Coverage

The core covers:

- PICO/PICOS/PECO framework terms: population, patient, intervention, exposure, comparator, control, outcome, study design, setting, follow-up, subgroup, and endpoint.
- Study designs: RCT, clinical trial, cohort, prospective and retrospective cohort, case-control, cross-sectional, nested case-control, case-cohort, diagnostic accuracy, prognostic, observational, real-world, and registry studies.
- Effect measures: HR, OR, RR, relative risk, RD, MD, SMD, WMD, correlation coefficient, beta coefficient, CI, SE, and p value.
- Survival and oncology outcomes: OS, PFS, DFS, RFS, EFS, CSS, DSS, ORR, CR, PR, SD, PD, recurrence, metastasis, and mortality.
- General clinical outcomes: incidence, prevalence, risk, hospitalization, adverse events, quality of life, symptom score, treatment response, and complications.
- Diagnostic accuracy terms: sensitivity, specificity, AUC, ROC, DOR, PLR, NLR, PPV, and NPV.
- Meta-analysis statistics: heterogeneity, I-squared, tau-squared, random-effects and fixed-effect models, subgroup analysis, sensitivity analysis, meta-regression, publication bias, funnel plot, Egger test, Begg test, and leave-one-out analysis.
- Publication and exclusion types: systematic review, meta-analysis, review, case report, letter, editorial, comment, conference abstract, protocol, animal study, in vitro study, and non-human study.
- Quality assessment tools: Cochrane Risk of Bias / RoB 2, ROBINS-I, Newcastle-Ottawa Scale / NOS, QUADAS-2, JBI critical appraisal, AHRQ checklist, and GRADE.

## Term Boundaries

Meta terms use `category=meta_analysis_term` and are not disease concepts. Effect measures and outcomes are separated:

- `HR`, `OR`, `RR`, `MD`, `SMD`, `WMD`, and `CI` are effect-measure terms.
- `OS`, `PFS`, `DFS`, `RFS`, `EFS`, `CSS`, `DSS`, `ORR`, `CR`, `PR`, `SD`, and `PD` are outcome terms.
- Diagnostic accuracy terms are kept in `diagnostic_accuracy_terms`, separate from general clinical outcomes.

Publication type and exclusion type overlap for some terms. For example, `case report` is a publication type and can also be used as an exclusion filter in Meta Analysis workflows.

## Context Isolation

In `meta_analysis` context, lookup may output PICO terms, study design terms, effect measures, outcome terms, diagnostic accuracy terms, publication and exclusion types, quality assessment terms, PubMed query terms, and MeSH terms.

In `bioinformatics` context, Meta-only outputs are filtered out. Short tokens such as `OS`, `HR`, `OR`, `RR`, `CI`, `MD`, `SMD`, `SE`, `PR`, `CR`, `SD`, and `PD` do not become Bioinformatics main outputs.

## Short Token Rules

Short uppercase tokens require exact uppercase token boundaries. This prevents:

- `OR` from matching the lowercase word `or`.
- `CI` from matching ordinary substrings inside longer text.
- `OS` from leaking into Bioinformatics data-type or disease outputs.

Ambiguous tokens such as `PR`, `SD`, and `PD` are retained with ambiguity warnings because they can mean partial response, stable disease, progressive disease, progesterone receptor, standard deviation, or Parkinson disease depending on context.

## Not Covered

This version does not implement a full Cochrane, MeSH Publication Type, EBM ontology, or statistical ontology import. It also does not produce final executable PubMed strategies; it only provides normalized shared vocabulary fields for downstream drafting.

## Next Steps

Recommended next stages:

- Cardiovascular Core v1.
- Immune Inflammatory Core v1.
- External ontology subset import for MeSH publication types, EBM terms, and quality appraisal tools.
