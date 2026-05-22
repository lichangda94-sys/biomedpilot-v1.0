# Bioinformatics B23.6 Survival / Clinical Report-Ready Section Package Planning Task

Date: 2026-05-22

## Goal

Plan the minimum gated section-ready package contract for KM/log-rank survival and Cox clinical association sections so the B23 full integrated report content gate can later distinguish:

- formal KM/Cox statistical sections that are eligible for section package export
- KM/Cox plot artifacts that are useful but not sufficient
- design/preflight/testing/imported clinical outputs that must remain blocked
- full integrated report readiness, which must remain blocked until all required section gates pass

This planning stage does not enable survival/clinical report-ready export and does not enable full integrated report export.

## Current Baseline

Current B23 gate behavior:

- `formal_deg`, `ora_enrichment`, and `gsea_preranked` can be evaluated through existing section report-ready gates.
- `survival_km_logrank` and `cox` are represented by placeholder gates.
- KM/Cox real plot artifacts can exist, but they do not make survival/clinical report-ready eligible.
- Full integrated report export remains blocked by `survival_clinical_report_ready_not_implemented`.
- Section-only packages cannot substitute for full integrated report completion.

Current blocking evidence:

- `full_integrated_prerequisite_survival_clinical_report_ready_missing:survival_km_logrank`
- `full_integrated_prerequisite_survival_clinical_report_ready_missing:cox`
- `survival_clinical_report_ready_not_implemented`

## B23.6.1 KM/log-rank Section-Ready Minimum Conditions

KM/log-rank section-ready should require all of the following:

- source result exists in result index v2
- `task_type=survival_km_logrank`
- `result_semantics=formal_computed_result`
- source result is produced only from B12/B13 gates
- validation status is `passed` or explicitly allowed `warning`
- dependency snapshot is present and `status=passed`
- parameters manifest is present and includes time column, event column, grouping rule, group labels, minimum group/event policy, censoring policy, and missing value policy
- task-run log artifact is present
- output table artifacts are present and registered
- KM/log-rank result table validation is passed
- p-value appears only as a statistical log-rank result, not clinical conclusion
- plot artifact is formal KM source-driven and registered, or an explicit table-only survival section mode is implemented and confirmed
- warnings, limitations, provenance, and low-event-count notes are included
- `report_ready_eligible` can become true only for the section package after the section gate passes

KM/log-rank blockers should include:

- missing source result
- non-formal result semantics
- imported/testing/exploratory/preflight source
- missing B12/B13 gate provenance
- missing or failed dependency snapshot
- missing parameter manifest
- missing task-run log
- missing result table
- failed result table validation
- low event count not acknowledged
- missing formal KM plot artifact when plot is required
- table-only mode not explicitly allowed
- clinical conclusion text detected

## B23.6.2 Cox Section-Ready Minimum Conditions

Cox section-ready should require all of the following:

- source result exists in result index v2
- `task_type=cox_univariate` for the MVP section
- Cox multivariate remains disabled/design-audit unless a later formal gate activates it
- `result_semantics=formal_computed_result`
- source result is produced only from B12/B14 gates
- validation status is `passed` or explicitly allowed `warning`
- dependency snapshot is present and `status=passed`
- parameters manifest is present and includes time column, event column, covariate id, covariate type, comparison rule, missing value policy, minimum event policy, tie handling, and confidence interval policy
- task-run log artifact is present
- output table artifacts are present and registered
- Cox result table validation is passed
- HR, CI, and p-value are presented only as statistical association outputs
- plot artifact is formal Cox source-driven and registered, or an explicit table-only Cox section mode is implemented and confirmed
- warnings, limitations, provenance, and low-event-count notes are included
- `report_ready_eligible` can become true only for the Cox section package after the section gate passes

Cox blockers should include:

- missing source result
- non-formal result semantics
- imported/testing/exploratory/preflight source
- missing B12/B14 gate provenance
- missing or failed dependency snapshot
- missing parameter manifest
- missing task-run log
- missing result table
- failed result table validation
- invalid covariate
- low event count not acknowledged
- Cox multivariate result provided where only univariate is enabled
- missing formal Cox plot artifact when plot is required
- table-only mode not explicitly allowed
- clinical conclusion text detected

## B23.6.3 Section Package Layout

KM and Cox section-ready packages should be section-only packages, not full integrated report packages.

Proposed layout:

- `survival_clinical_report_package/<timestamp>_<section_id>/`
- `section_report.md`
- `README_limitations.md`
- `tables/`
- `plots/`
- `manifests/`
- `logs/`
- `provenance/`

Required manifests:

- section report-ready gate snapshot
- source result index snapshot
- parameter manifest snapshot
- dependency snapshot
- table validation snapshot
- plot artifact manifest or explicit table-only mode manifest
- warnings and limitations manifest
- task-run log copy
- package inventory

## B23.6.4 UI Requirements

The UI should show KM and Cox section-ready as independent gates before full integrated report export.

Required UI states:

- KM/log-rank section package: disabled until KM section gate passes
- Cox section package: disabled until Cox section gate passes
- Cox multivariate: disabled/design-audit unless later formal gate activates it
- Full integrated report: disabled until DEG, ORA, GSEA, KM, and Cox section gates all pass
- Disabled reasons visible for missing dependency, missing confirmation/parameter manifest, low event count, missing plot/table-only confirmation, invalid source semantics, and missing provenance

The UI must not imply that KM/Cox plots, preflight rows, or design audits are report-ready.

## B23.6.5 Full Integrated Report Unblock Conditions

The full integrated content gate can remove `survival_clinical_report_ready_not_implemented` only after all of the following exist and pass:

- `evaluate_km_logrank_report_ready_gate`
- `create_km_logrank_report_ready_package`
- `evaluate_cox_report_ready_gate`
- `create_cox_report_ready_package`
- section-ready result-index write-back for KM/Cox section packages
- UI disabled reasons for KM/Cox section report-ready gates
- tests proving preflight/testing/imported/exploratory sources are blocked
- tests proving clinical conclusion/prognosis/treatment advice text is absent
- full integrated gate tests proving section-only packages remain distinct from full integrated packages

Even after survival/clinical section-ready gates pass, full integrated export still requires:

- all five required sections present
- all five section report-ready gates passed
- renderer gate passed for the requested export format
- package layout and non-overwrite policy passed
- warnings, limitations, and provenance included

## B23.6.6 DEG_TASK_PLAN Integration Import Surface Note

Integration reported that full `python3 -m pytest -q tests/bioinformatics` collection was blocked by an import error for `app.bioinformatics.deg_task_plan.DEG_TASK_PLAN`.

This can be modified as an independent import surface blocker when it appears in the receiving branch:

- restore or add `DEG_TASK_PLAN = Path("manifests") / "analysis_tasks" / "deg_task_plan.json"`
- keep the value compatible with existing task-run manifests
- do not change DEG runtime behavior
- do not activate formal DEG paths
- run the collection-blocking tests again before attributing later failures to B23 work

In this ReleaseBuild worktree, `DEG_TASK_PLAN` is already present, so B23.6 does not need to alter the file.

## Suggested Implementation Order

1. Add survival/clinical section report-ready gate data models.
2. Add KM/log-rank report-ready gate tests for pass/block cases.
3. Add Cox univariate report-ready gate tests for pass/block cases.
4. Add package skeletons that write only after section gates pass.
5. Add UI gate preview and disabled reasons.
6. Update full integrated gate to consume real KM/Cox section gates.
7. Run full bioinformatics/UI/package/open-W/codesign validation.

## Non-Goals

- No full integrated report export activation.
- No clinical conclusion, prognosis, or treatment recommendation.
- No survival/clinical full report beyond section-only packages.
- No Cox multivariate formal activation.
- No risk score or nomogram.
- No GSEA or DEG expansion.
- No dependency auto-install.
