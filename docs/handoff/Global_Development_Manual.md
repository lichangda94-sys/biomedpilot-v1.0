# BioMedPilot Global Development Manual

Version date: 2026-05-13

This manual applies to BioMedPilot / 医研智析 v1.0 worktrees. It defines the default development boundaries for Codex tasks so repeated task prompts do not need to restate the same safety, testing, and reporting rules.

## 1. Project Positioning

BioMedPilot / 医研智析 is a Developer Preview / internal beta / local testing build.

It is not production-ready, not clinical-grade, and not submission-grade. UI labels, reports, task outputs, and handoff documents must keep this distinction clear.

Do not describe draft, dry-run, testing-level, imported, or preflight outputs as formal computed results.

## 2. Local Worktree Structure

The v1.0 local root is:

```text
/Users/changdali/Developer/biomedpilot v1.0
```

Worktrees:

- `MainLine`: stable mainline, shell, login, module selection, settings, testing mode, Bioinformatics stable flow, shared interfaces, minimal Meta entry.
- `Bioinformatics`: Bioinformatics Analysis development.
- `Meta`: Meta Analysis workflow development.
- `Vocabulary`: shared medical vocabulary and query intelligence vocabulary work.
- `UIShell`: desktop shell and unified UI work.
- `LabTools`: basic laboratory tools module.
- `AI`: AI Gateway, local model integration, privacy policy, audit policy.
- `Integration`: staged merges, conflict handling, full validation, internal test preparation.
- `ReleaseBuild`: internal release packaging worktree.

Do not edit `_repo.git` directly.

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

## 14. Manual Review Boundaries

When in doubt, stop and ask before:

- Changing module ownership.
- Deleting data.
- Pushing to remote.
- Handling credentials.
- Enabling AI or external network behavior.
- Reclassifying result maturity.
- Making irreversible changes.
