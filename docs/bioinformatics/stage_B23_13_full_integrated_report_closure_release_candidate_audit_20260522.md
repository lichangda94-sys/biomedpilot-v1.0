# Bioinformatics B23.13 Full Integrated Report Closure / Release Candidate Audit

Date: 2026-05-22

## Scope

This audit closes the B23 full integrated report track in ReleaseBuild after commit `fcf987c` and checks whether the current candidate can keep the full integrated report capability as a release-candidate snapshot.

The audit covers:

- B23.1-B23.12 implementation state
- full integrated report gate and markdown package export
- renderer format gate
- survival/clinical section package prerequisite convergence
- Results Browser UX and disabled reasons
- result semantics and provenance boundaries
- ReleaseBuild smoke/package/open-W/codesign checks
- untracked file boundary

This audit does not enable PDF/DOCX, clinical conclusions, risk score/nomogram, or additional analysis engines.

## B23 Stage Acceptance Table

| Stage | Scope | Status | Acceptance Notes |
|---|---|---:|---|
| B23.1 | Full integrated report gate | Passed | Gate requires DEG/ORA/GSEA/KM/Cox sections and blocks missing/non-formal sources. |
| B23.2 | Package skeleton | Passed | Stable markdown package layout under `report_package/integrated/`; copies registered artifacts only. |
| B23.3 | UI preview / disabled reasons | Passed | Results Browser shows gate, package plan, renderer state, and section rows. |
| B23.4 | Renderer format gate | Passed | Markdown renderer enabled; PDF/DOCX blocked with explicit renderer disabled reasons. |
| B23.5 | Content prerequisite gate | Passed | Full integrated report requires section prerequisites, result semantics, dependency, validation, task logs, and source tables. |
| B23.6 | Survival/clinical section package planning | Passed | KM/Cox section-ready minimum conditions defined before full report convergence. |
| B23.7 | Survival/clinical report-ready gate skeleton | Passed | KM/log-rank and Cox univariate gates validate formal result, tables, dependency, provenance, and no clinical conclusion. |
| B23.8 | Survival/clinical section package skeleton | Passed | KM/Cox section-only packages write tables, manifests, logs, provenance, and limitations. |
| B23.9 | Survival/clinical section package UI | Passed | Results Browser and Analysis Center expose KM/Cox section package gates and disabled reasons. |
| B23.10 | Section prerequisite unblock planning | Passed | Validated KM/Cox section packages can satisfy full integrated survival/clinical prerequisites. |
| B23.11 | Markdown export activation gate | Passed | Full integrated markdown export activates only when all five section prerequisites pass. |
| B23.12 | UX / acceptance audit | Passed | UI shows markdown-only, PDF/DOCX disabled, output path, section provenance, and limitations. |

## Gate Closure Findings

The full integrated report backend now has these required gates:

- all required sections requested: formal DEG, ORA, GSEA, KM/log-rank, Cox univariate
- required section results present
- `result_semantics=formal_computed_result`
- result index v2 fields present
- validation status passed or warning
- dependency snapshot passed
- task-run logs present
- source output tables present
- section report-ready gates passed
- KM/Cox section package integrity validation passed
- no imported/testing/exploratory/preflight source included

When all section prerequisites pass:

- `status=eligible_for_full_integrated_report`
- `export_activation_status=eligible_for_markdown_export`
- `enabled_export_formats=["markdown"]`
- `disabled_export_formats=["pdf", "docx"]`

When prerequisites do not pass:

- `full_integrated_report_export_waiting_for_section_prerequisites` is emitted.

## Package / Provenance Findings

The markdown full integrated package contains:

- `integrated_report.md`
- `README_limitations.md`
- `integrated_report_package_manifest.json`
- `sections/`
- `tables/`
- `plots/`
- `manifests/`
- `logs/`
- `provenance/`
- gate snapshot
- result index snapshot
- section manifest
- dependency snapshot
- warnings/limitations manifest
- package inventory

Artifacts are copied only from registered result index `output_artifacts`, `plot_artifacts`, and `log_artifacts`. The package does not consume temporary runner files or unregistered outputs.

## UI / UX Findings

Results Browser now shows:

- full integrated report status
- markdown-only availability
- PDF/DOCX disabled reason
- renderer status and renderer id
- enabled and disabled export formats
- section rows for DEG/ORA/GSEA/KM/Cox
- section package validation status
- prerequisite status
- blockers
- limitations and no-clinical-conclusion boundary
- output path after package creation

The UI copy does not claim clinical diagnosis, prognosis, treatment recommendation, risk score, or nomogram.

## Boundary Findings

Preserved boundaries:

- PDF/DOCX full integrated export remains disabled.
- Imported/testing/exploratory/preflight results cannot enter full integrated package.
- Section-only KM/Cox packages are not relabeled as full integrated packages.
- Clinical conclusions remain forbidden.
- Risk score/nomogram remains disabled.
- No dependency auto-install action is added.
- No GSEA/survival/clinical extra analysis beyond previously gated MVP surfaces is enabled by this audit.

## ReleaseBuild Candidate State

Current branch:

- `codex/releasebuild-formal-deg-carryover`

Current audited baseline before this document:

- `fcf987c clarify Bioinformatics integrated report export UX`

Untracked file boundary:

- `docs/release/ReleaseBuild_handoff_report_20260513.md` remains untracked and must not be included in the Bioinformatics B23 closure commit.

## Issues

### Blocker

- None found.

### Major

- None found.

### Minor

- PDF/DOCX remain intentionally disabled and require a future renderer/export acceptance stage.
- Full integrated report is markdown-only and statistical-research-only.

## Validation

Commands run for this closure:

- `git status --short --branch`
- `git rev-parse HEAD`
- `git branch --show-current`
- `git diff --check`
- `python3 -m pytest tests/bioinformatics -q -k "integrated or report or survival_clinical_report_ready or km or cox or survival or clinical or analysis_ui"`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "report or results_browser or analysis_task or survival or cox"`
- `python3 -m pytest tests/bioinformatics -q`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
- `python3 -m app.main --smoke-test`
- `python3 scripts/package_app.py --smoke-test`
- `open -W -n dist/BioMedPilot.app --args --smoke-test`
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`

Results:

- `git status --short --branch`: branch `codex/releasebuild-formal-deg-carryover`; only this audit document and excluded untracked `docs/release/ReleaseBuild_handoff_report_20260513.md` are untracked before commit.
- `git rev-parse HEAD`: `fcf987cbc4698ce9654de8cd155bb190d00a5ab6`
- `git branch --show-current`: `codex/releasebuild-formal-deg-carryover`
- `git diff --check`: passed
- B23 broad bio filter: `187 passed, 466 deselected in 1.84s`
- B23 broad UI filter: `18 passed, 96 deselected in 3.54s`
- full `tests/bioinformatics`: `653 passed in 5.87s`
- full `tests/ui`: `271 passed in 39.90s`
- source smoke: passed, `launch_mode=source`, `git_head=fcf987c`
- package smoke: passed, `launch_mode=packaged-local-python`, `signing_status=ad_hoc_signed`, `code_signed=true`
- open-W smoke: passed
- codesign: passed, `dist/BioMedPilot.app: valid on disk` and satisfies its Designated Requirement

## Final Conclusion

Conclusion: **Release-candidate acceptable with known markdown-only boundary**.

B23 full integrated report is complete for the current MVP definition:

- markdown-only package export
- five-section prerequisite gate
- auditable package layout
- section provenance
- result semantics protection
- UI disabled reasons and output path visibility
- no clinical conclusions

## Recommendations

Recommended next step:

- Keep the current ReleaseBuild branch as the candidate snapshot after final validation passes.

Optional future stages:

- B24 Renderer Expansion Planning for PDF/DOCX.
- ReleaseBuild formal handoff note update, excluding stale untracked handoff files unless explicitly refreshed.
