# Workbench Demo Acceptance Checklist

This checklist defines the minimum internal demo acceptance bar for the unified Workbench shell.

## Environment

- [ ] Repository path is `/Users/changdali/Documents/model9`.
- [ ] Branch is `feature/unified-workbench-shell`.
- [ ] App can be imported and compiled.
- [ ] Full pytest passes.
- [ ] `git diff --check` passes.
- [ ] `git status --short` is clean after commit.

## Startup

- [ ] Desktop entry starts successfully.
- [ ] Workbench home is visible.
- [ ] Bioinformatics and Meta Analysis entries are visible.
- [ ] Navigation does not trigger analysis, runner, export, or network behavior.

## Demo Project

- [ ] Demo project can be created.
- [ ] Project manifest is written.
- [ ] `profile_readiness.json` is written.
- [ ] Demo content is stable and deterministic.
- [ ] Demo content does not depend on network access or external data files.

## Meta Analysis Workspace

- [ ] Meta Analysis workspace can be opened.
- [ ] Profile Analysis Readiness panel is visible.
- [ ] Readiness table displays the demo profiles.
- [ ] The disclaimer is visible.
- [ ] The disclaimer makes clear that readiness is not pooled statistical output.
- [ ] Unsupported and unimplemented features are visible.

## Row Editing / CSV Template

- [ ] Profile Row Editor table is visible.
- [ ] Row editor note says edits are not auto-saved.
- [ ] Row editor can persist rows only through explicit project-file save/load APIs.
- [ ] `Save rows` writes project-local CSV only.
- [ ] `Load rows` reads project-local CSV only.
- [ ] Row editor shows unsaved-change state.
- [ ] Row editor shows structural validation issue count.
- [ ] Invalid rows are blocked from explicit project-file save.
- [ ] Loading over dirty rows is blocked until a discard-confirmation path is used.
- [ ] Row editor note says no statistics, workflow execution, or report export is triggered.
- [ ] CSV templates are limited to:
  - `TREATMENT_EFFECT_META`
  - `DIAGNOSTIC_ACCURACY_META`
  - `BIOMARKER_PREVALENCE_ASSOCIATION_META`
- [ ] CSV template export/import helpers pass tests.
- [ ] Project-local row CSV persistence writes under `profile_rows/`.

## Safety Boundaries

- [ ] No UI action runs `AnalysisService`.
- [ ] No UI action runs a statistical runner.
- [ ] No NMA, HSROC, metaprop, or GLMM is implemented.
- [ ] No AI/PDF extraction is implemented.
- [ ] No PDF/Word export is implemented.
- [ ] No complex dashboard drill-down is implemented.
- [ ] No all-10-profile editing UI is implemented.

## Validation Commands

```bash
python3 -m compileall -q core reporting app tests
./.venv/bin/python -m pytest -q
git diff --check
```

## Acceptance Decision

- [ ] Accept for internal demo.
- [ ] Defer demo until blocking issues are fixed.

Blocking issues:

| issue | severity | owner | decision |
| --- | --- | --- | --- |
|  |  |  |  |
