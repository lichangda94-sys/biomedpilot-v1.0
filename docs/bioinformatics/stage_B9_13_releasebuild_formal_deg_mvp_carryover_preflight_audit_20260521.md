# Bioinformatics B9.13 ReleaseBuild Formal DEG MVP Carry-over Preflight Audit

Date: 2026-05-21

## Scope

This is a preflight audit only. It checks whether ReleaseBuild can receive the Formal DEG MVP from MainLine baseline `be8c924336f42e92e89eb1d8d7710bed02d4cd99` (`carry over Bioinformatics formal DEG MVP to MainLine`).

No ReleaseBuild publication was performed. No desktop entry point was overwritten. No GSEA, survival, formal clinical statistics, or report-ready bypass was enabled.

## ReleaseBuild Current State

- Worktree: `/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild`
- Branch: `dev/release-internal-test`
- HEAD: `639abf8f2b66e1226c0f199a8b3cd68403fd3ae5`
- Git status: clean except existing untracked `docs/release/ReleaseBuild_handoff_report_20260513.md`
- `git diff --check`: passed
- MainLine baseline: `be8c924336f42e92e89eb1d8d7710bed02d4cd99`
- Merge-base with MainLine baseline: `67e5b138ae38c2350caf7d19d7724f018653f92b`

ReleaseBuild and MainLine baseline are divergent. ReleaseBuild is not an ancestor of `be8c924`, and `be8c924` is not an ancestor of ReleaseBuild HEAD. This is not a fast-forward carry-over.

## Difference Summary vs MainLine be8c924

Relevant scoped diff from ReleaseBuild HEAD to MainLine `be8c924` covers 198 paths and about 30k insertions / 3.9k deletions across Bioinformatics, package/runtime config, tests, and docs.

High-risk non-Bioinformatics effects in a direct merge:

- `scripts/package_app.py` differs and must be reconciled with ReleaseBuild packaging/signing behavior.
- `app/main.py` lacks formal DEG runtime check flags in ReleaseBuild.
- `pyproject.toml`, `requirements.txt`, and `config/bioinformatics/package_requirements.yaml` differ.
- A direct MainLine diff includes deletions of several ReleaseBuild/LabTools/Meta UI tests; this is not acceptable as an unscoped carry-over.

## Formal DEG MVP File Coverage

Critical B8/B9 formal DEG MVP files missing from current ReleaseBuild:

- `app/bioinformatics/deg_engine/formal_runner.py`
- `app/bioinformatics/deg_engine/runtime_validation.py`
- `app/bioinformatics/deg_engine/parameter_gate.py`
- `app/bioinformatics/analysis_ui/state.py`
- `app/bioinformatics/analysis_ui/action_rules.py`
- `app/bioinformatics/results/registry.py`
- `app/bioinformatics/reports/formal_deg.py`
- `app/bioinformatics/plots/formal_deg.py`
- `tests/bioinformatics/test_formal_controlled_deg_runner.py`
- `tests/bioinformatics/test_formal_deg_runtime_validation.py`
- `tests/bioinformatics/test_analysis_ui_state.py`

Scoped formal DEG / analysis UI / result-report-plot diff count:

- Added in MainLine baseline relative to ReleaseBuild: 49 files
- Modified relative to ReleaseBuild: 3 files

Recognition / standardization contract convergence is not present in ReleaseBuild and needs scoped carry-over:

- `app/bioinformatics/analysis_inputs/*` missing
- `app/bioinformatics/project_recognition.py` differs
- `app/bioinformatics/project_standardization.py` differs
- `app/bioinformatics/standardization_confirmation.py` differs
- `app/bioinformatics/deg_task_plan.py` differs
- `tests/bioinformatics/test_analysis_input_resolver.py` missing
- `tests/bioinformatics/test_workflow_adapters.py` differs

## Package / Runtime / Codesign Risk

Current ReleaseBuild package preflight:

- `python3 scripts/package_app.py --smoke-test`: passed
- `open -W -n dist/BioMedPilot.app --args --smoke-test`: passed
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`: passed

Controlled runtime was found at:

- `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/.venv-b9-3b/bin/python`

Controlled runtime imports:

- numpy `2.4.6`
- pandas `3.0.3`
- scipy `1.17.1`
- statsmodels `0.14.6`
- architecture `arm64`

Controlled runtime package smoke:

- `python3 scripts/package_app.py --python ".../.venv-b9-3b/bin/python" --smoke-test`: passed
- Smoke reported `pyside6_available=False`, so this controlled runtime is suitable for dependency import validation but not a complete ReleaseBuild GUI runtime.

Formal DEG runtime check gap:

- ReleaseBuild `app.main` only supports `--smoke-test`.
- `--bio-formal-deg-runtime-check` produced no `/tmp/biomedpilot_releasebuild_formal_deg_runtime.json`.
- This is expected before carry-over and is a major gap for B9.3/B9 formal DEG validation.

## Test Results

Commands run from ReleaseBuild:

- `git status`: only existing untracked `docs/release/ReleaseBuild_handoff_report_20260513.md`
- `git branch --show-current`: `dev/release-internal-test`
- `git rev-parse HEAD`: `639abf8f2b66e1226c0f199a8b3cd68403fd3ae5`
- `git diff --check`: passed
- `python3 -m pytest tests/bioinformatics -q -k "formal_deg_e2e or formal_deg_report or formal_deg_plot or formal_controlled_deg or parameter_confirmation or analysis_ui"`: pytest exit code 5, `312 deselected`; no matching formal DEG / analysis UI tests exist in current ReleaseBuild
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q -k "bioinformatics"`: 112 passed, 137 deselected
- `python3 -m app.main --smoke-test`: passed, `git_head=639abf8`
- `python3 scripts/package_app.py --smoke-test`: passed
- `open -W -n dist/BioMedPilot.app --args --smoke-test`: passed
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`: passed
- `python3 scripts/package_app.py --python ".../.venv-b9-3b/bin/python" --smoke-test`: passed with `pyside6_available=False`
- `open -W -n dist/BioMedPilot.app --args --bio-formal-deg-runtime-check --bio-formal-deg-runtime-check-output /tmp/biomedpilot_releasebuild_formal_deg_runtime.json`: open returned 0 but runtime output JSON was not created

## Findings

Blockers:

- None for starting a scoped ReleaseBuild carry-over execution.
- Direct fast-forward or direct broad merge is not recommended because ReleaseBuild and MainLine diverged and the MainLine diff would remove unrelated ReleaseBuild/LabTools/Meta tests.

Major:

- Formal DEG MVP modules, tests, analysis UI state/action rules, result registry, formal report gate, plot artifact modules, and runtime validation are absent from current ReleaseBuild.
- ReleaseBuild lacks the `--bio-formal-deg-runtime-check` app entry point.
- ReleaseBuild has not incorporated B9.12a recognition / standardization / resolver contract convergence.
- Controlled runtime has DEG dependencies but lacks PySide6, so it should not be treated as the full ReleaseBuild desktop runtime.

Minor:

- Existing untracked `docs/release/ReleaseBuild_handoff_report_20260513.md` must remain uncommitted unless separately audited.
- Current ReleaseBuild package smoke and codesign are healthy before carry-over.

## Carry-over Recommendation

Recommendation: proceed to ReleaseBuild carry-over execution, but use a scoped carry-over strategy rather than fast-forward or unfiltered merge.

Carry-over type:

- Fast-forward: not possible.
- Direct merge: not recommended.
- Scoped carry-over: recommended.
- No carry-over: not necessary; preflight shows package baseline is healthy and gaps are well-scoped.

Minimum scoped carry-over should include:

- B9.12a recognition / standardization convergence files
- B8/B9 analysis input resolver and DEG-ready gates
- Formal DEG dependency/parameter/result schema/runtime modules
- Analysis UI state/action rules and UI wiring
- Result registry, formal plot artifact, formal report-ready package modules
- `app/main.py` formal DEG runtime check args
- `scripts/package_app.py` reconciliation without regressing ReleaseBuild signing/executable naming
- dependency files and tests needed for B9 formal DEG MVP validation

Do not carry over unrelated test deletions or project_storage artifacts.

## Rollback Plan

Before carry-over execution:

1. Keep this audit commit as the ReleaseBuild preflight checkpoint.
2. Start carry-over on a new local branch from `dev/release-internal-test`.
3. Stage only scoped Bioinformatics/runtime/package files.
4. If validation fails, reset the carry-over branch to the audit checkpoint and keep `dev/release-internal-test` unchanged.

After carry-over execution:

1. Re-run full ReleaseBuild source tests, UI tests, package smoke, open smoke, codesign, and formal DEG runtime check.
2. If package/open/codesign fails, inspect launcher logs and package metadata before any ReleaseBuild publication.
3. Do not publish until formal DEG runtime JSON reports passed in the packaged app.

## Next Command Suggestions

Recommended execution outline:

```bash
cd "/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild"
git switch -c codex/releasebuild-formal-deg-carryover
git checkout be8c924 -- app/bioinformatics/analysis_inputs app/bioinformatics/analysis_ui app/bioinformatics/deg_engine app/bioinformatics/deg_ready app/bioinformatics/plots app/bioinformatics/results app/bioinformatics/reports app/bioinformatics/project_recognition.py app/bioinformatics/project_standardization.py app/bioinformatics/standardization_confirmation.py app/bioinformatics/deg_task_plan.py app/main.py config/bioinformatics/package_requirements.yaml pyproject.toml requirements.txt tests/bioinformatics tests/ui/test_bioinformatics_workflow_pages.py
```

Then reconcile `scripts/package_app.py` manually instead of blindly replacing ReleaseBuild packaging behavior.

Required post-carry-over validation:

```bash
git diff --check
python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
python3 -m app.main --smoke-test
python3 scripts/package_app.py --smoke-test
open -W -n dist/BioMedPilot.app --args --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
open -W -n dist/BioMedPilot.app --args --bio-formal-deg-runtime-check --bio-formal-deg-runtime-check-output /tmp/biomedpilot_releasebuild_formal_deg_runtime.json
```

## Conclusion

B9.13 preflight audit passes as an audit. ReleaseBuild is not ready for direct formal DEG MVP receipt, but it is ready to begin a scoped ReleaseBuild carry-over execution from MainLine `be8c924`, with explicit protection for ReleaseBuild packaging/signing behavior and unrelated tests.
