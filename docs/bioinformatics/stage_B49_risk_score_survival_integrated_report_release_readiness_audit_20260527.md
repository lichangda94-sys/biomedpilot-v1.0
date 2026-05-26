# Bioinformatics B49 Risk Score / Survival Clinical Integrated Report Release-Readiness Audit

Date: 2026-05-27

## Scope

B49 audits the ReleaseBuild candidate after B46-B48 risk score validation and survival / clinical integrated report UX hardening.

This audit covers:

- B46 risk score validation section report-ready gate and package.
- B47 optional risk score validation full integrated report prerequisite.
- B48 Results Browser UX for risk score section package and explicit full integrated inclusion.
- KM/log-rank and Cox section package prerequisites.
- Full integrated report package provenance, limitations, and disabled reasons.
- ReleaseBuild smoke, package, LaunchServices `open -W`, and codesign readiness.

This audit does not add new algorithms, clinical interpretation, automatic risk grouping, cutoff selection, treatment advice, public release promotion, or renderer policy changes.

## Candidate Baseline

| Item | Value |
| --- | --- |
| Branch | `codex/releasebuild-formal-deg-carryover` |
| Audited baseline | `ba17b16c7947574cabf415f09ce89b8f0f06148b` |
| Previous stage | B48 `harden risk score integrated report UX gates` |
| Excluded untracked file | `docs/release/ReleaseBuild_handoff_report_20260513.md` |

## Stage Acceptance

| Stage | Scope | Status | Acceptance Notes |
| --- | --- | ---: | --- |
| B46 | Risk score validation section gate/package | Passed | Requires formal risk score result, dependency snapshot, validation, task log, result table, calibration/DCA statistics, B42 nomogram, and B45 plots or explicit table-only mode. |
| B47 | Optional risk score full integrated prerequisite | Passed | `risk_score_validation` participates only when explicitly included through `include_sections` or `section_result_ids`; package prerequisite is validated before full integrated eligibility. |
| B48 | Results Browser UX hardening | Passed | UI shows risk score section gate, table-only checkbox, disabled reasons, and full integrated explicit inclusion checkbox. |
| B49 | Release-readiness closure audit | Passed | No blocker found; candidate remains release-candidate acceptable for statistical research package workflows with clinical boundaries retained. |

## Risk Score Section Gate Findings

Risk score validation section package remains gated by:

- `task_type=risk_score`
- `result_semantics=formal_computed_result`
- result index v2 fields
- dependency snapshot `status=passed`
- validation status `passed` or `warning`
- task-run log artifact
- `risk_score_result_table`
- calibration statistics table
- decision curve statistics table
- B42 nomogram plot artifact
- B45 calibration and decision curve plot artifacts, unless explicit table-only section mode is selected
- no clinical conclusion text

Package creation writes a section-only package with:

- `risk_score_validation_report.md`
- `README_limitations.md`
- `tables/`
- `plots/`
- `manifests/`
- `logs/`
- `provenance/`
- gate snapshot
- source result entry
- parameters manifest
- dependency snapshot
- table validation
- plot artifact manifest
- warnings / limitations
- package inventory

The source risk score result may record `report_ready_eligible=True` only after the section package is created. This is section package eligibility, not full integrated automatic inclusion and not clinical validation.

## Full Integrated Inclusion Findings

Default full integrated report sections remain:

- formal DEG
- ORA enrichment
- preranked GSEA
- KM/log-rank survival
- Cox clinical association

Risk score validation is optional and excluded by default.

When explicitly selected, the UI passes:

- `include_sections=[formal_deg, ora_enrichment, gsea_preranked, survival_km_logrank, cox, risk_score_validation]`
- `section_result_ids={"risk_score_validation": <selected risk score result id>}` when available

The full integrated gate blocks explicit risk score inclusion until the B46 section package integrity validation passes. Expected blockers include:

- `full_integrated_prerequisite_survival_clinical_section_package_not_passed:risk_score_validation`
- `section_package_artifact_missing:risk_score_validation:risk_score_validation_only`

## Survival / Clinical Section Package Findings

KM/log-rank and Cox section-only packages still satisfy full integrated prerequisites only after package integrity validation passes.

Validated boundaries:

- Section-only package scope remains distinct from `full_integrated_report`.
- KM/Cox/risk score packages carry `clinical_conclusion_enabled=False`.
- Section packages do not independently enable full integrated export.
- Survival/clinical packages must include provenance, warnings, limitations, dependency snapshot, task log, and result index snapshot.

## UI / UX Findings

Results Browser now exposes:

- KM/log-rank section report-ready row.
- Cox section report-ready row.
- Risk score validation section report-ready row.
- Risk score table-only mode checkbox.
- Risk score section package generation button.
- Full integrated report explicit `risk_score_validation` inclusion checkbox.
- Full integrated section rows, package plan, renderer status, disabled reasons, and output path.

UX safeguards:

- Risk score validation is not included by default.
- Risk score validation must be explicitly selected before full integrated inclusion.
- Missing risk score package, dependency, validation, artifact, or plot/table-only requirements are surfaced as blockers.
- Status copy says statistical research only and forbids clinical diagnosis, prognosis, risk group, validated risk score interpretation, and treatment recommendation.

## Package / Provenance Findings

Full integrated package remains markdown-first and writes:

- `integrated_report.md`
- `README_limitations.md`
- `integrated_report_package_manifest.json`
- `sections/`
- `tables/`
- `plots/`
- `manifests/`
- `logs/`
- `provenance/`
- full integrated gate snapshot
- result index snapshot
- section manifest
- dependency snapshot
- warnings / limitations
- package inventory

Artifacts are copied only from registered result index artifacts. Temporary runner files, preflight outputs, imported/testing/exploratory results, and legacy-only outputs are still forbidden sources.

## Renderer / Desktop Candidate Findings

Markdown package export remains enabled after full integrated prerequisites pass.

Rendered DOCX/PDF exports remain package-renderer artifacts and are not analysis results. This audit does not change the renderer policy:

- DOCX depends on user-system Pandoc detection and explicit renderer activation paths.
- PDF remains disabled pending the PDF activation stage.
- No bundled Pandoc, XeLaTeX, wkhtmltopdf, Quarto, or network download policy change is introduced here.

Desktop candidate checks passed through source smoke, package smoke, `open -W`, and codesign.

## Boundary Findings

Preserved boundaries:

- No automatic risk score inclusion.
- No clinical diagnosis.
- No prognosis conclusion.
- No treatment recommendation.
- No risk group or cutoff generation.
- No validated risk score interpretation.
- No imported/testing/exploratory/preflight result upgrade.
- No GSEA/survival/clinical capability expansion.
- No renderer policy expansion.
- No legacy formal execution bypass.

## Issues

### Blocker

- None found.

### Major

- None found.

### Minor

- Risk score validation full integrated inclusion is optional and requires explicit UI selection; this is intentional but should remain visible in release notes.
- PDF remains disabled by policy.
- DOCX remains governed by renderer gate and external Pandoc availability.
- `docs/release/ReleaseBuild_handoff_report_20260513.md` remains untracked and excluded from this Bioinformatics closure commit.

## Validation

Commands run:

| Command | Result |
| --- | --- |
| `git diff --check` | Passed |
| `python3 -m pytest tests/bioinformatics -q -k "integrated_report or risk_score or survival_clinical or report_ready"` | Passed: `138 passed, 630 deselected` |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "full_integrated or survival_clinical_section_report or results_browser"` | Passed: `13 passed, 107 deselected` |
| `python3 -m pytest tests/bioinformatics -q` | Passed: `768 passed, 1 warning` |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` | Passed: `282 passed` |
| `python3 -m app.main --smoke-test` | Passed: source smoke, `git_head=ba17b16` |
| `python3 scripts/package_app.py --smoke-test` | Passed: packaged-local-python smoke, `git_head=ba17b16`, `code_signed=true` |
| `open -W -n dist/BioMedPilot.app --args --smoke-test` | Passed |
| `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app` | Passed: app valid on disk and satisfies designated requirement |

Warning observed:

- `tests/bioinformatics/test_geo_differential_expression_runner.py::test_geo_deg_runner_uses_explicit_gsm_group_assignments` emitted a scipy precision-loss runtime warning for nearly identical data. This is a known statistical warning in the fixture path and not a B49 regression.

## Final Conclusion

Conclusion: **Release-candidate acceptable for the current statistical research report surface**.

B49 passes with no blocker or major issue. The candidate supports auditable section package and full integrated markdown package workflows for DEG / ORA / GSEA / KM / Cox, with optional risk score validation inclusion only after explicit user selection and prerequisite package validation.

The candidate is still not a clinical-use system and does not produce clinical conclusions, risk-group recommendations, prognosis claims, or treatment advice.

## Recommendation

Recommended next step:

- Keep the current ReleaseBuild branch as the candidate snapshot.
- If continuing development, proceed to a scoped B50 release handoff / internal-test gate refresh, without including stale untracked handoff files unless explicitly regenerated and reviewed.
