# Development Task Queue

This file records active and completed development tasks for future Codex sessions.

## UI shell baseline for unified BioMedPilot platform and Bioinformatics workspace

Status: completed on `feature/unified-workbench-shell`.

Scope:

- Add unified Workbench startup shell for BioMedPilot / 医研智析.
- Add Bioinformatics workspace baseline with navigation, mock dashboard, placeholders, and disabled analysis settings.
- Add Meta Analysis workspace placeholder shell without refactoring existing Meta services.
- Keep real GEO / TCGA / GTEx download, analysis, Meta statistics, and report export out of scope.

Validation commands:

```bash
python -m compileall -q app tests/test_project_navigation_model.py tests/test_workbench_shell.py
QT_QPA_PLATFORM=minimal python -m pytest -q tests/test_project_navigation_model.py tests/test_workbench_shell.py
QT_QPA_PLATFORM=minimal python -m pytest -q
git diff --check
```

Result:

- Completed with one task commit.
- See `docs/ui_design_implementation_plan.md` for component boundaries and follow-up integration order.

## UI integration readiness and future shell migration

Status: completed on `feature/unified-workbench-shell` as a minimum integration pass.

Current recommendation:

- Do not continue UI behavior changes until the active functional chain is stable.
- Do not merge `feature/unified-workbench-shell` into `main` as a default entry replacement.
- Keep the Workbench shell as a future integration candidate and preserve existing tested UI surfaces.
- Treat the profile readiness/reporting work as a separate mainline that must be integrated deliberately, not assumed to exist on this branch.

Planning document:

- `docs/ui_integration_readiness_audit.md`

Current branch baseline:

- Branch: `feature/unified-workbench-shell`.
- Audited base HEAD before this roadmap update: `18e02e9 docs: record UI integration readiness audit`.
- Full pytest baseline on this branch: `491 passed`.
- The later profile readiness/reporting baseline of `736 passed` belongs to a different commit line and is not currently merged here.

Suggested UI integration order:

1. Unified Workbench shell stabilization. Completed with stable workspace/page state accessors and Qt tests.
2. Project navigation and project open/create/save connection. Completed with project manifest storage and explicit `MainWindow` methods.
3. Reporting readiness read-only panel connection. Completed with project-local `profile_readiness.json` loading and a read-only Meta workspace panel.
4. Demo project loader. Completed with a local demo Meta readiness project seeder.
5. Profile row CSV template import/export. Completed for the first three integration profiles: treatment effect, diagnostic accuracy, and biomarker prevalence/association.
6. Minimal profile row editing UI. Completed as a template-driven Meta workspace table without persistence or execution buttons.

Explicit non-goals for the next UI integration phase:

- No statistical runner work.
- No NMA, HSROC, `metaprop`, or GLMM.
- No AI/PDF extraction.
- No PDF/Word export.
- No complex dashboard drill-down.
- No simultaneous editing UI for all 10 Meta profiles.

Suggested next action:

- Review whether the Workbench shell should remain an optional entry or become the default entry after the profile readiness/reporting branch is reconciled.
- Desktop entry baseline now presents BioMedPilot / 医研智析, workspace entries, internal testing notice, project actions, current project state, Meta workflow navigation, readiness panel, and row CSV actions. Next, run a manual internal demo walkthrough before adding discard-confirmation dialogs or broader profile editors.
