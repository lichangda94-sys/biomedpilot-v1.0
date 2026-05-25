# Bioinformatics B32-B40 Formal Analysis / Production Report Roadmap

Date: 2026-05-25

Branch: `codex/releasebuild-formal-deg-carryover`

Baseline: `d08aca5 docs(bio): plan risk score nomogram contracts`

## Scope

This roadmap plans the remaining work needed to move Bioinformatics from the current gated MVP / section-package candidate into broader formal analysis and production-grade report capabilities.

The plan is intentionally staged. It must not bypass the existing B8/B9 resolver/result semantics contracts, and it must not turn clinical interpretation into a free-text conclusion layer before validation, provenance, and review gates exist.

## Current Implemented Base

The current ReleaseBuild candidate already includes:

- B8/B9 resolver, formal DEG gates, result index v2 contracts.
- Formal DEG MVP plus R backends: limma, DESeq2, edgeR.
- Multi-factor DEG through method-specific Rscript gates.
- ORA controlled enrichment.
- Preranked GSEA controlled MVP.
- KM/log-rank controlled MVP.
- Cox univariate and Cox multivariate controlled workflows.
- Real SVG plot artifacts for DEG / ORA / GSEA / KM / Cox where gated.
- Section-only and full integrated report package gates.
- DOCX and PDF rendered export package artifacts through external renderer detection.
- Analysis Center capability map and disabled reasons.
- B31 risk score / nomogram contract planning.

## Remaining Capability Gaps

| Gap | Current State | Desired Final State |
| --- | --- | --- |
| Risk score / nomogram | B21/B31 design audit only | Controlled validated risk score table, optional nomogram/calibration artifacts, review/report package |
| Clinical conclusions | Forbidden | Guarded, reviewed interpretation layer with no treatment advice and explicit evidence/provenance |
| Full clinical interpretation | Not implemented | Statistical interpretation summaries with uncertainty, limitations, and source traceability |
| Legacy formal execution | Forbidden | Either stays blocked or is reimplemented through B8/B9 contracts, never copied directly |
| Complex clinical statistics | Limited KM/Cox | Multi-endpoint, subgroup, interaction, association models behind gates |
| Advanced enrichment | Controlled ORA/GSEA only | Audited msigdbr/clusterProfiler-like resources, collections, phenotype/permutation policy where valid |
| Production-grade report | Package/provenance first | Reviewed narrative report with tables, plots, limitations, citations/provenance, renderer outputs |
| Prediction model system | Not formal | Training/validation, calibration, decision curve, external validation, model card |
| External dependencies | Detect-first only | User-managed or optionally bundled policy per dependency with package/open-W/codesign validation |

## Non-Negotiable Architecture Rules

1. All formal inputs must come through standardized repositories, registries, or `analysis_input_repository`.
2. No runner may read recognition reports or UI temporary tables as formal analysis input.
3. Every formal result must register in result index v2.
4. Every formal result needs parameters manifest, dependency snapshot, task-run log, validation status, warnings, and blockers.
5. Imported/testing/exploratory/preflight outputs must never be upgraded to `formal_computed_result`.
6. Plot artifacts inherit source result semantics.
7. Report packages may include only section-ready or full-gate-ready formal sources.
8. Clinical diagnosis, treatment recommendation, and unsupported prognosis claims remain forbidden until a separate reviewed medical-interpretation policy exists.
9. External dependencies remain detect-first unless a dedicated packaging policy stage explicitly changes that.
10. Legacy logic must be recontracted, not copied into formal execution.

## Phase B32: Risk Score Source / Contract Gate

Goal: make risk score readiness auditable without executing a model.

Deliverables:

- `risk_score_nomogram_contract_gate.py`
- tests for source Cox multivariate result, clinical variable audit, coefficient provenance, training/validation split, cutoff policy, validation plan
- Analysis Center gate rows for risk score source readiness
- explicit disabled reasons

Allowed:

- validate source result
- validate model design
- show candidate variables and blockers

Forbidden:

- compute risk score
- generate risk groups
- generate nomogram
- write result index
- create report-ready package

Exit criteria:

- B31/B32 gate returns `ready_for_parameter_confirmation` only when all source/design checks pass.
- UI still keeps risk score execution disabled.

## Phase B33: Risk Score Parameter Confirmation / Result Schema

Goal: define user confirmation and future result schema before execution.

Deliverables:

- risk score parameter confirmation manifest
- result schema gate for future risk score result
- model card skeleton
- validation/calibration policy schema

Minimum confirmed fields:

- source Cox multivariate result id
- coefficients
- variables
- scaling/transformation policy
- missingness/imputation policy
- training cohort
- validation cohort
- cutoff policy
- calibration plan
- overfitting protection
- clinical-boundary acknowledgement

Exit criteria:

- parameter confirmation can pass
- result schema gate can validate a candidate bundle
- execution remains disabled until B34

## Phase B34: Controlled Risk Score Execution MVP

Goal: compute a statistical risk score table from an audited Cox multivariate source.

Deliverables:

- controlled executor
- risk score result table
- result index v2 registration
- task-run log
- dependency snapshot
- validation summary

Allowed outputs:

- sample id
- risk score numeric value
- model variables used
- missingness flags
- validation status

Conditionally allowed:

- risk group label only if cutoff policy was confirmed and validation gate passes; label must be statistical grouping, not clinical prognosis.

Forbidden:

- diagnosis
- treatment recommendation
- survival probability claim unless separately modeled/validated
- automatic clinical conclusion
- report-ready by default

Exit criteria:

- controlled fixture passes
- no fake statistics
- no imported/preflight source accepted
- UI shows result review, not clinical conclusion

## Phase B35: Nomogram / Calibration / Decision Curve Renderer

Goal: add visualization artifacts for validated risk score results.

Deliverables:

- nomogram renderer plan and gate
- calibration plot artifact gate
- decision curve analysis planning gate
- renderer dependency snapshot
- artifact manifest registration

Allowed:

- plot artifacts from formal validated risk score result only
- SVG/PNG/PDF artifact registration
- calibration curve if validation data exists

Forbidden:

- creating plot from design audit
- clinical recommendation from plot
- full report-ready unlock by plot alone

Exit criteria:

- formal risk score plot artifacts register with inherited semantics
- renderer failure is graceful and does not corrupt result

## Phase B36: Risk Score Review / Section Report-Ready Gate

Goal: let users inspect risk score output and optionally package a section-only risk score report.

Deliverables:

- risk score result review
- risk score table export
- provenance panel
- risk score section report-ready gate
- risk score section package

Required package contents:

- score table
- model card
- parameters confirmation
- dependency snapshot
- validation summary
- plot artifact manifest if plots exist
- limitations
- provenance

Boundary:

- still no treatment advice
- no “patient prognosis” label unless a future B38 interpretation policy allows scoped wording

Exit criteria:

- section package is independently auditable
- full integrated report inclusion remains gated

## Phase B37: Advanced Enrichment Expansion

Goal: expand ORA/GSEA beyond controlled MVP without losing reproducibility.

Candidate capabilities:

- curated gene-set resource registry
- msigdbr-like local resource import
- collection/version/species/gene-id gates
- clusterProfiler-compatible result schema planning
- optional phenotype permutation policy when sample labels and methods support it
- multi-collection enrichment review

Required gates:

- gene set version
- species
- gene id mapping
- background universe
- multiple testing policy
- method compatibility
- source DEG/GSEA result semantics

Exit criteria:

- advanced enrichment remains formal only when all resources are versioned and registered
- no pathway clinical interpretation

## Phase B38: Clinical Statistics Expansion

Goal: add broader formal clinical statistical models behind explicit gates.

Candidate capabilities:

- multi-endpoint survival
- subgroup analysis
- interaction terms
- categorical/continuous clinical association models
- competing risk planning
- time-dependent covariate planning
- multiple-testing correction across clinical endpoints

Required controls:

- endpoint definition manifest
- subgroup manifest
- model family compatibility
- minimum event/sample constraints
- missingness and censoring policy
- multiplicity policy
- interpretation guard

Exit criteria:

- statistical outputs can be reviewed
- no clinical recommendations
- no automated patient-level medical conclusion

## Phase B39: Production Report Interpretation Layer

Goal: move from provenance package to production-grade statistical report narrative.

Deliverables:

- interpretation block schema
- evidence/provenance citation per statement
- limitation statement generator
- contradiction/warning surfacing
- reviewer approval state
- report text validation for forbidden clinical language

Allowed statements:

- descriptive statistical findings
- method limitations
- data quality warnings
- uncertainty and multiple-testing caveats

Forbidden unless separately reviewed:

- diagnosis
- treatment choice
- patient prognosis
- clinical actionability

Exit criteria:

- report narrative is generated only from section-ready formal sources
- every claim links to source result/table/plot/provenance
- clinical boundary scanner blocks forbidden language

## Phase B40: Dependency Packaging / Release Policy Upgrade

Goal: decide whether selected external dependencies should remain system-managed or become packaged/managed.

Candidates:

- R runtime
- Bioconductor packages
- Pandoc
- TinyTeX/XeLaTeX
- Python modeling libraries
- plotting libraries

Decision matrix:

- license
- package size
- codesign/notarization impact
- architecture support
- update policy
- offline behavior
- user installation path
- source/package/open-W consistency

Exit criteria:

- each dependency has an explicit policy: system-required, bundled, optional, detect-only, or unsupported
- package/open-W/codesign tests pass for any policy change

## Final Production Readiness Gate

The final production-grade report should require:

1. all selected formal analyses have result index v2 entries
2. all input packages are standardized and resolver-backed
3. all dependency snapshots pass
4. all parameter confirmations are current
5. all result tables validate
6. all plots are registered artifacts
7. all report sections pass section-ready gates
8. all narrative claims pass provenance and forbidden-language checks
9. external dependencies pass source/package/open-W/codesign acceptance
10. the package can be independently audited without project temp files

## Suggested Execution Order

1. B32 risk score source / contract gate
2. B33 risk score parameter confirmation and result schema
3. B34 controlled risk score execution MVP
4. B35 nomogram/calibration/decision-curve renderer gates
5. B36 risk score review and section report-ready package
6. B37 advanced enrichment expansion
7. B38 clinical statistics expansion
8. B39 production report interpretation layer
9. B40 dependency packaging/release policy upgrade
10. final production readiness closure audit

## Commit / Release Policy

Each phase should be independently committed and auditable. No phase should depend on untracked `docs/release/ReleaseBuild_handoff_report_20260513.md` or `project_storage` artifacts.

Package/open-W/codesign must run whenever UI, app launcher, renderer, dependency detection, or packaged runtime behavior changes.

## Conclusion

The next concrete implementation task should be B32 Risk Score Source / Contract Gate. It is the lowest-risk way to begin turning risk score / nomogram from design-audit-only into a formal future capability without prematurely creating clinical claims or unsupported prediction outputs.
