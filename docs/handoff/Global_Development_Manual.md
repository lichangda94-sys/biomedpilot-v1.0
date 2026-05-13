# BioMedPilot Global Development Manual

Version date: 2026-05-13

This manual applies to BioMedPilot / 医研智析 v1.0 worktrees. It defines the default development boundaries for Codex tasks so repeated task prompts do not need to restate the same safety, testing, and reporting rules.

## 1. Project Positioning

BioMedPilot / 医研智析 is a Developer Preview / internal beta / local testing build.

It is not production-ready, not clinical-grade, and not submission-grade. UI labels, reports, task outputs, and handoff documents must keep this distinction clear.

Do not describe draft, dry-run, testing-level, imported, or preflight outputs as formal computed results.

## 2. Local Development Root And Worktree Structure

The v1.0 local root is:

```text
/Users/changdali/Developer/biomedpilot v1.0
```

This local root is the development management layer. It contains the bare repository, worktrees, migration bundles, local project control documents, handoff documents, and archive material.

`MainLine` is only one worktree under this root. It is the stable mainline code workspace, not the whole development management layer.

`_repo.git` is the bare repository. Do not edit code in `_repo.git` directly.

Worktrees:

- `MainLine`: stable mainline, desktop shell, stable entry points, shared interfaces, Bioinformatics stable flow, minimal Meta entry, and current testable baseline.
- `Bioinformatics`: Bioinformatics module development for GEO / TCGA / GTEx / local expression data. It must not perform PubMed literature retrieval.
- `Meta`: Meta Analysis workflow development for PICO, search strategy, literature library, deduplication, screening, full text, extraction, quality assessment, statistics, and reporting. It must not perform GEO / TCGA / GTEx data analysis.
- `Vocabulary`: shared medical vocabulary, query intelligence vocabulary work, context isolation, audit, and tests.
- `UIShell`: desktop shell, login, main window, module selection, navigation, theme, and visual consistency. It must not change business logic.
- `LabTools`: basic laboratory tools module. It must not pollute Bioinformatics or Meta project manifests.
- `AI`: AI Gateway, local model integration, privacy policy, audit policy, and disabled-by-default AI capability.
- `Integration`: staged merges, conflict handling, cross-module validation, and full or staged test verification. It must not be used for large feature development.
- `ReleaseBuild`: internal test packaging, package metadata validation, and packaged smoke tests. It must not be used for feature development.

Support directories at the v1.0 local root:

- `Archive`: migration bundle, historical snapshots, old material, or external archive material.
- `00_HandoffDocs`: cross-stage handoff material when used by the project control flow.
- `01_ProjectControl`: local control documents, migration reports, global manual, and stage control material.

## 2.1 MainLine, Integration, And Release Flow

Module work may happen in module worktrees. Before module work becomes part of the stable baseline:

1. Run the module worktree's required tests.
2. Update the module stage report, handoff, or audit document.
3. Enter `Integration` or an equivalent integration validation flow.
4. Verify cross-module behavior, UI entry points, boundaries, and result labels.
5. Merge only validated work into `MainLine`.
6. Use `ReleaseBuild` only from a validated MainLine or validated release source.

An internal beta or packaged test build must not be produced directly from an unvalidated single module worktree.

## 3. Business Module Boundaries

### Bioinformatics

Bioinformatics supports GEO / TCGA / GTEx / local expression data analysis assistance.

It may handle data entry, dataset search for bioinformatics data sources, retrieval, download, adapters, recognition, standardization, analysis setup, task center, results, and reports for expression-oriented workflows.

It must not perform PubMed literature retrieval as Bioinformatics data search.

### Meta

Meta supports PICO / PICOS / PECO, search strategy, literature library, deduplication, screening, full text management, extraction, quality assessment, statistics, and reporting.

It must not perform GEO / TCGA / GTEx expression data analysis.

### LabTools

LabTools supports basic laboratory utilities such as dilution, concentration, qPCR, Western blot, ELISA helpers, cell counting, and experiment records.

It must not pollute Bioinformatics or Meta project manifests.

## 4. Shared Capability Boundaries

Shared capabilities include AI Gateway, query intelligence, shared medical vocabulary, project center, data center, task center, report center, environment checks, localization, config, rules, audit, and packaging support.

Shared code must not become a hidden business workflow. Business-specific workflow decisions belong to the relevant module.

Shared search, report, task, and data-entry infrastructure must remain infrastructure. Bioinformatics search and Meta search have different meanings and must stay inside their modules. Shared report center code may provide common interfaces, manifests, export helpers, or audit fields, but it must not write Bioinformatics, Meta, or LabTools business conclusions.

## 5. Required Reading Before Each Codex Development Task

Before changing files, Codex must read:

- The current worktree `CODEX.md`.
- `/Users/changdali/Developer/biomedpilot v1.0/README_总说明.md`.
- This `Global_Development_Manual.md`.
- The current stage report, handoff, cleanup audit, migration report, or task-specific audit file relevant to the request.

Memory notes may guide defaults, but repo-local files and the active checkout define the current executable instructions.

## 6. Continuous Execution Authorization

When the user gives a clear stage task, Codex may continue within that task scope without asking for confirmation for each small step.

Within the authorized scope, Codex may:

- Read files.
- Modify in-scope code or documents.
- Add or adjust in-scope tests.
- Run required tests.
- Fix failures exposed by those tests when the fix is clearly in the same scope.
- Update relevant documentation.
- Commit the in-scope changes after validation passes.

Codex must stop and request human confirmation when:

- The task scope needs to expand.
- Another worktree or another module must be modified.
- The task requires deleting tests, legacy directories, data assets, example projects, historical audit files, or other high-risk content.
- The task requires `git push`, remote overwrite, force push, remote branch deletion, or similar remote write operations.
- The task requires GitHub authentication, SSH keys, tokens, passwords, or credential handling.
- Tests fail and there are multiple plausible product or technical directions for the fix.
- A merge conflict appears and the correct side cannot be selected mechanically.
- A module boundary would change, such as adding PubMed to Bioinformatics or GEO / TCGA / GTEx to Meta.
- AI, local models, external network, downloading, automatic screening, automatic analysis, or automatic final reporting would be enabled.
- User data, project data, or real analysis results would be deleted or rewritten.
- Draft, dry-run, or testing-level output would be reclassified as real result or production-ready.
- Continuing may create irreversible impact.

## 7. General Prohibitions

- Do not modify across worktrees unless explicitly authorized.
- Do not bypass AI Gateway.
- Do not save raw prompt or raw response.
- Do not generate fake DEG, fake statistics, fake figures, or fake reports.
- Do not describe dry-run or testing-level outputs as real results.
- Do not mix PubMed literature retrieval into Bioinformatics.
- Do not mix GEO / TCGA / GTEx data analysis into Meta.
- Do not delete current effective tests.
- Do not expose large amounts of manifest, schema, branch, or raw path detail in the main UI.
- Do not expose large amounts of asset id, internal manifest, schema, branch, raw path, or debug detail in the ordinary main UI; use developer diagnostics when this information is needed.
- Do not produce clinical conclusions.
- Do not claim production-ready status.

## 8. Testing Principles

Run tests for the active worktree and the changed surface.

Minimum defaults:

- MainLine: `python3 -m app.main --smoke-test`, `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`, `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q`, `git diff --check`.
- Bioinformatics: `python3 -m app.main --smoke-test`, `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q`, `git diff --check`.
- Meta: `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/meta_analysis -q`, `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`, `python3 -m app.main --smoke-test`, `git diff --check`.
- Vocabulary: run vocabulary audit plus relevant `tests/shared` vocabulary and query intelligence tests, then `git diff --check`.
- UIShell: run `tests/ui`, smoke test, and `git diff --check`.
- LabTools: run `tests/labtools` and smoke test; if `tests/labtools` does not exist, create a minimal test before adding behavior.
- AI: run relevant AI Gateway tests and smoke test; keep AI disabled by default.
- Integration: run staged integration tests or full validation appropriate to the merge scope.
- ReleaseBuild: run packaging smoke and packaged app smoke when release packaging changes.

If a task explicitly narrows verification, follow the user request but report residual risk.

## 9. Commit Requirements

- Use one clear commit per stage or coherent task.
- Use conventional prefixes such as `fix`, `feat`, `docs`, `test`, `refactor`, or `chore`.
- Commit only in-scope files.
- Preserve unrelated user changes.
- After committing, report commit hash, changed files, test results, risks, and worktree status.

## 10. Cleanup And Slimming Rules

- Audit first, archive second, delete low-risk files last.
- Do not directly delete current tests.
- Do not directly delete legacy directories.
- Audit legacy dependencies before moving or deleting legacy code.
- Historical audit reports should be archived before deletion.
- Prefer `docs/archive/` or the v1.0 root `Archive/` for historical material.
- Treat tracked logs, generated test data, example projects, and old snapshots as human-confirmation items unless a cleanup stage explicitly authorizes them.

## 11. Documentation Update Rules

Update the relevant handoff, stage report, or audit document when any of the following changes:

- Migration status.
- Module boundaries.
- Test baseline.
- Stage completion state.
- Known issues.
- Cleanup or archive decisions.
- AI / local model policy.
- Reporting or result semantics.

Documentation must not overstate maturity. Use precise labels such as draft, dry-run, testing-level, imported result, preflight, or real computed result.

## 12. AI And Local Model Rules

- AI is disabled by default.
- Local model access must go through AI Gateway.
- AI may generate drafts or suggestions only.
- User confirmation is required before AI output enters retrieval, screening, extraction, analysis, or reporting workflows.
- AI must not automatically execute downloads, screening, analysis, or final report generation.
- Do not save raw prompts or raw responses.
- Store only necessary audit summaries when required.
- External network capability must be declared by module and should require user confirmation by default.
- Enabling AI, local model access, external network access, downloads, automatic screening, automatic analysis, or final report generation is a manual review boundary.

## 13. Reports And Results Rules

Reports and UI output must clearly distinguish:

- `draft`
- `dry-run`
- `testing-level`
- `preflight`
- `imported result`
- `real computed result`

Do not write clinical conclusions.

Do not claim production-ready, clinical-grade, or submission-grade status.

Imported results must be labeled as imported. Dry-run task records must not be presented as completed analysis. Preflight manifests must not be presented as DEG execution.

## 14. Feature Status Rules

Feature status must be explicit in UI, reports, handoff documents, and stage reports when relevant.

Allowed status labels include:

- 可用 / `available`
- 测试级 / `testing-level`
- 草稿 / `draft`
- 待确认 / `pending confirmation`
- 阻塞 / `blocked`
- 未接入 / `not connected`
- 开发者预览 / `developer preview`

Do not present testing-level, draft, pending, blocked, or not connected features as generally available.

## 15. Data, Cache, And Git Rules

The following should not enter Git by default:

- User project data.
- Downloaded datasets.
- PDFs.
- Intermediate analysis outputs.
- Runtime caches.
- Python and pytest caches.
- Build and packaging outputs.
- Local runtime logs.

Small, explainable, reproducible `tests/fixtures` may be tracked. Demo projects may be tracked only when they are small, explainable, reproducible, and do not contain real user data.

Tracked logs, generated test data, example projects, historical audits, old snapshots, and legacy directories are manual-confirmation items unless a cleanup stage explicitly authorizes their handling.

## 16. Packaging And Internal Beta Rules

Before packaging or internal beta handoff, record and verify:

- `git_head`
- `branch`
- `build_time`
- `app_version`
- `enabled_modules`
- `feature_flags`
- Developer Preview / internal beta labeling
- smoke test result
- whether unfinished or testing-level features are included

Internal beta and packaged builds must not come directly from an unvalidated single module worktree. Use validated MainLine or ReleaseBuild sources.

## 17. MainLine Entry Conditions

Work may enter MainLine only after:

- Module tests pass.
- Relevant UI or integration tests pass.
- No cross-module pollution is introduced.
- Documentation or stage reports are updated.
- Result maturity labels are clear.
- AI Gateway and module boundaries are respected.
- Integration or an equivalent validation flow has confirmed the merge surface.

## 18. Manual Review Boundaries

When in doubt, stop and ask before:

- Changing module ownership.
- Deleting data.
- Pushing to remote.
- Handling credentials.
- Enabling AI or external network behavior.
- Enabling automatic downloads, screening, analysis, or final reporting.
- Reclassifying result maturity.
- Making irreversible changes.
