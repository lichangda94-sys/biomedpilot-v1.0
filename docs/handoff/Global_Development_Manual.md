# BioMedPilot Global Development Manual

Version date: 2026-05-13

This manual applies to BioMedPilot / 医研智析 v1.0 worktrees. It defines the default development boundaries for Codex tasks so repeated task prompts do not need to restate the same safety, testing, and reporting rules.

## 0. File Authority And Conflict Handling

`/Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/Global_Development_Manual.md` is the highest-priority development rule document for BioMedPilot v1.0 local work.

`/Users/changdali/Developer/biomedpilot v1.0/MainLine/docs/handoff/Global_Development_Manual.md` is the MainLine handoff copy of the same manual. It must stay byte-for-byte synchronized with the `01_ProjectControl` copy whenever both files exist.

If a task prompt, module handoff, stage report, branch note, or Codex memory conflicts with this manual, Codex must stop before editing and report the conflict to the human owner. Task-specific instructions may narrow scope, but they must not override the safety, privacy, medical, Git, release, or module-boundary rules in this manual without explicit human confirmation.

When this manual is updated, the update must be treated as a governance change. The change should include a handoff or audit note that records what was already covered, what was added, what still needs human confirmation, and what was intentionally not modified.

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

- `MainLine`: stable mainline, desktop shell, login, module selection, stable entry points, shared interfaces, Bioinformatics stable flow, minimal Meta entry, and current testable baseline. It is not a large feature development branch.
- `Bioinformatics`: Bioinformatics module development for GEO / TCGA / GTEx / local expression data. It must not perform PubMed literature retrieval.
- `Meta`: Meta Analysis workflow development for PICO, search strategy, literature library, deduplication, screening, full text, extraction, quality assessment, statistics, and reporting. It must not perform GEO / TCGA / GTEx data analysis.
- `Vocabulary`: shared medical vocabulary, query intelligence vocabulary work, context isolation, audit, and tests.
- `UIShell`: desktop shell, login, main window, module selection, navigation, theme, and visual consistency. It must not change business logic.
- `LabTools`: basic laboratory tools module for calculators, unit conversion, formulas, experiment utilities, and future image analysis helpers. It must not pollute Bioinformatics or Meta project manifests.
- `AI`: AI Gateway, local model integration, privacy policy, audit policy, and disabled-by-default AI capability. It is the only approved model-call boundary.
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

LabTools supports basic laboratory utilities such as concentration calculation, dilution, unit conversion, reagent or formula lookup, qPCR, Western blot, ELISA helpers, cell counting, fluorescence intensity, gray value analysis, scratch assay analysis, ImageJ / Fiji / OpenCV assisted workflows, and experiment records.

It must not pollute Bioinformatics or Meta project manifests.

LabTools must not be mixed into Bioinformatics or Meta. Experimental calculators, lab formulas, image-analysis helpers, scratch assays, cell counting, fluorescence quantification, and gray-value workflows belong to LabTools even when the biological context overlaps with a Bioinformatics or Meta project.

Image analysis outputs must record algorithm name, software or library version where available, thresholding / segmentation / preprocessing parameters, input provenance, and a clear manual-review requirement. They must be described as measurement assistance unless a later validated workflow explicitly upgrades the status.

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

Mandatory preflight checklist before editing:

1. Confirm `pwd` and the intended local root or worktree path.
2. Confirm the active worktree with `git rev-parse --show-toplevel` when inside a worktree, or with `git --git-dir _repo.git worktree list --porcelain` from the v1.0 local root.
3. Confirm the current branch with `git branch --show-current` when inside a worktree.
4. Run `git status --short` for the relevant worktree. For cross-worktree governance tasks, inspect all relevant worktrees and record any unrelated dirty files.
5. Read the root README and this global manual.
6. Read the relevant module's latest handoff, audit, cleanup, baseline, architecture, testing, or packaging document before changing that module's documents or code.
7. Decide whether the task touches cross-module behavior, AI Gateway, model calls, networking, privacy, real analysis execution, real statistics execution, file deletion, file migration, merging, packaging, release wording, credentials, or remote operations.
8. If the task changes both the project-control manual and the MainLine handoff copy, run `cmp` after editing and keep both copies synchronized.

Codex must not rely on stale branch notes when the v1.0 root, worktree list, or global manual show newer structure. Older documents that mention pre-v1.0 paths are historical unless explicitly refreshed.

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

### 6.1 Mandatory Stop And Report Table

Codex must stop before editing or continuing when any of the following occurs:

| Situation | Required action |
| --- | --- |
| The task conflicts with this global manual. | Report the conflict and wait for human decision. |
| The expected path, worktree, or branch does not match the task. | Report the observed path / branch and wait. |
| `git status --short` shows unknown or unexpected uncommitted changes in files relevant to the task. | Report the files and do not overwrite them. |
| The task requires cross-module modification not already authorized. | Report affected modules and wait. |
| The task requires real Bioinformatics executor integration. | Report the proposed executor, inputs, outputs, tests, and safety plan. |
| The task requires real Meta statistics executor integration. | Report the proposed method, assumptions, validation baseline, and safety plan. |
| The task requires external network access, database retrieval, API calls, or downloads. | Report target services, data types, and confirmation boundary. |
| The task requires saving raw prompts, raw responses, sensitive source text, credentials, or patient-level data. | Stop; do not save the content without explicit policy approval. |
| Tests fail and the fix is not clearly within the task scope. | Report failure, likely cause, and options. |
| The task requires merge, push, force push, remote branch changes, credential handling, deletion, migration, or high-risk cleanup. | Report and wait for explicit authorization. |
| A requested output would imply diagnosis, treatment, clinical decision support, or individual-patient interpretation. | Refuse that interpretation and keep output within research-assistance wording. |

## 7. General Prohibitions

| Prohibition | Scope |
| --- | --- |
| Do not modify across worktrees unless explicitly authorized. | Git / module isolation |
| Do not create cross-module pollution. | Bioinformatics, Meta, Vocabulary, AI, UIShell, LabTools, Integration |
| Do not bypass AI Gateway. | AI, local model, external model |
| Do not save raw prompt or raw response. | AI privacy and audit |
| Do not enable network access, external APIs, database retrieval, or downloads by default. | Networking and data retrieval |
| Do not generate fake DEG, fake statistics, fake figures, fake screening decisions, fake PRISMA counts, or fake reports. | Scientific integrity |
| Do not describe dry-run, imported, preflight, draft, or testing-level outputs as real computed results. | UI, reports, docs |
| Do not describe testing-level features as production-ready, clinical-grade, or submission-grade. | Release and maturity wording |
| Do not mix PubMed literature retrieval into Bioinformatics. | Module boundary |
| Do not mix GEO / TCGA / GTEx data analysis into Meta. | Module boundary |
| Do not put LabTools calculators or image-analysis workflows into Bioinformatics or Meta manifests. | Module boundary |
| Do not delete current effective tests, legacy directories, audit reports, handoff docs, or high-risk files without explicit cleanup authorization. | Cleanup |
| Do not expose large amounts of asset id, internal manifest, schema, branch, raw path, raw JSON, queue path, or debug detail in the ordinary main UI. | UI governance |
| Do not produce clinical conclusions, diagnoses, treatment recommendations, or individual-patient decisions. | Medical safety |
| Do not push, merge, force push, delete remote branches, or handle credentials without explicit authorization. | Git and remote safety |

## 7.1 UI Governance Authority

UI Governance / UI Design Principles is the authoritative basis for BioMedPilot cross-module interface development. If Bioinformatics, Meta Analysis, LabTools, or any later module UI development conflicts with the global UI principles, follow the global UI principles first; modules may adapt to their business workflows, but must not introduce conflicting colors, fonts, button systems, page structures, or visual styles.

明确规则：UI Governance / UI Design Principles 是 BioMedPilot 跨模块界面开发的权威依据。Bioinformatics、Meta Analysis、LabTools 或任何后续模块的 UI 开发，如果与总 UI 规范冲突，应优先遵循总 UI 规范；模块可以做业务适配，但不得自行引入冲突的颜色、字体、按钮体系、页面结构或视觉风格。

The global UI direction is Apple-like macOS premium biomedical research desktop software. The shared UI baseline uses the unified shell, unified navigation, unified status labels, shared tokens, and the following fixed core palette unless a later approved UI governance document changes it:

- Deep navy: `#12324A`
- Teal: `#1BAE9F`
- Light gray background: `#F5F7F9`
- White: `#FFFFFF`

Modules must not define independent theme systems, independent primary colors, independent button hierarchies, independent global navigation, or page structures that conflict with the global Shell. Warning, error, ready, draft, confirmed, and testing state colors must come from shared UI tokens instead of page-local hardcoding.

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

For documentation-only governance changes, the minimum verification is:

- `git diff --check`
- `cmp` between the project-control manual and the MainLine handoff manual when both are present and expected to match.
- `git status --short` for the relevant worktree before commit.

Full business tests may be skipped for documentation-only changes only when no business code, runtime config, package script, or test file is modified. The audit or handoff must state why business tests were not run.

## 9. Commit Requirements

- Use one clear commit per stage or coherent task.
- Use conventional prefixes such as `fix`, `feat`, `docs`, `test`, `refactor`, or `chore`.
- Commit only in-scope files.
- Preserve unrelated user changes.
- After committing, report commit hash, changed files, test results, risks, and worktree status.
- Do not commit unrelated dirty files that existed before the task.
- Do not push unless the user explicitly asks for push and credential / remote-write boundaries are clear.

Git, branch, worktree, merge, and release rules:

- Do not edit inside `_repo.git`.
- Do not treat the v1.0 local root as a normal worktree.
- Enter the intended worktree before code or tracked-document changes.
- Use the module branch that matches the task scope.
- Use `Integration` or an equivalent integration validation flow for staged cross-module merges.
- Keep `MainLine` stable and testable; do not use it as a large feature branch.
- Use `ReleaseBuild` only for packaging validation and packaged smoke tests.
- Merge only validated work into `MainLine`.
- Do not create internal test packages from an unvalidated single module worktree.
- Do not push, force push, rewrite remote history, or delete remote branches without explicit authorization.

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

## 16. Network, Database, And External Download Rules

Network access is disabled by default as a product capability and must not be enabled casually by development tasks.

External services include PubMed / NCBI, GEO, TCGA / GDC, GTEx, Crossref, DOI services, publisher sites, model providers, package mirrors, and any other remote API or download source.

Before adding or enabling network access, Codex must document:

- Module owner and purpose.
- Target service, endpoint class, and data types.
- User confirmation point.
- Cache location and Git exclusion.
- Privacy risk and sensitive data handling.
- Timeout, retry, error handling, and rate-limit behavior.
- Audit fields that prove what was requested without storing sensitive raw text unnecessarily.
- Tests or mocks that avoid live-network dependency by default.

External downloads must not be written into Git by default. Downloaded datasets, PDFs, full text, intermediate outputs, caches, and runtime logs belong in ignored project storage or user-selected external locations unless a small reproducible fixture is explicitly approved.

## 17. Real Bioinformatics Executor Gate

Real Bioinformatics analysis executor integration means code that runs or orchestrates real DEG, enrichment, correlation, survival, pathway, TCGA / GTEx, GSEA, plotting, or similar computational analysis beyond preflight, import, recognition, or dry-run manifest creation.

Before a real executor is connected, Codex must stop and require human confirmation of:

- Executor identity, version, dependency source, and local runtime requirements.
- Accepted input schema and validation rules.
- Output schema, result status, and reproducibility metadata.
- Test fixtures and expected results from known inputs.
- Failure handling, partial-output handling, and audit logging.
- How results are labeled as testing-level or real computed result.
- How researcher review is required before interpretation.

Fake analysis outputs are prohibited. Preflight manifests, task records, imported results, and dry-run assets must not be presented as completed real analyses.

## 18. Real Meta Statistics Executor Gate

Real Meta statistics executor integration means code that performs or delegates pooled effect estimation, heterogeneity, subgroup, sensitivity, diagnostic accuracy, publication-bias, forest/funnel output, or other statistical calculations intended to support a Meta Analysis result.

Before a real Meta statistics executor is connected or upgraded, Codex must stop and require human confirmation of:

- Statistical method and assumptions.
- Effect types supported and excluded.
- Confirmed analysis-plan entrypoint.
- Validation data and expected numerical baselines.
- Versioned output schema and audit manifest.
- How adjusted / unadjusted mixing, zero cells, outcome/timepoint mismatch, and insufficient study counts are handled.
- How results remain testing-level until reviewed.
- How no medical conclusion or final interpretation is generated automatically.

Meta statistical results must come from confirmed extraction and confirmed analysis plans. They must not be generated from AI text, PubMed candidate previews, or unconfirmed screening/extraction drafts.

## 19. Medical, Research, Ethics, And Clinical Safety

BioMedPilot is research-assistance software. It does not provide diagnosis, treatment recommendations, clinical decision support, individual-patient interpretation, or emergency guidance.

Bioinformatics and Meta Analysis outputs must be reviewed by qualified researchers before use. Public database findings, expression analyses, pooled estimates, AI suggestions, and literature summaries must not be directly interpreted as conclusions for an individual patient.

Reports and UI text should use cautious wording such as "suggests", "may indicate", "requires researcher review", "testing-level", "candidate", "draft", or "not clinically validated" when appropriate. Avoid definitive clinical language.

Ethics and privacy boundaries:

- Do not request, store, or upload patient-identifiable data unless an explicit approved workflow exists.
- Do not upload sensitive research content to external models or APIs without explicit approval.
- Do not imply IRB / ethics approval, regulatory clearance, or clinical validation.
- Keep audit trails sufficient for research review without storing unnecessary raw sensitive content.

## 20. Stage Report, Handoff, And Audit Writing Rules

Stage reports, handoff documents, cleanup reports, baseline documents, and audit reports must be precise, dated, and scoped.

Each report should state:

- Date.
- Scope and worktree.
- Current branch or relevant path.
- What existed before the task.
- What changed in the task.
- What was intentionally not modified.
- Verification commands and results.
- Remaining risks or human-confirmation items.
- Whether business tests were skipped and why.
- Whether any unrelated dirty files were present and left untouched.

Reports must not delete or rewrite historical evidence. Historical documents may be archived with an index in a dedicated cleanup stage, but should not be silently removed.

## 21. Packaging, Version, And Release Wording Rules

Developer Preview, internal beta, local testing build, testing-level, draft, preflight, imported result, and real computed result are distinct labels.

Packaging tasks must record or verify:

- `git_head`
- branch or source path
- `app_version`
- `app_channel`
- build time
- enabled modules
- feature flags
- smoke-test result
- whether the tested build is source or packaged
- whether the desktop app entry point has been refreshed when required

Do not call a build production-ready, clinical-grade, submission-grade, validated, certified, or release-ready unless a later explicit release-governance process defines and confirms that status.

`ReleaseBuild` may produce internal test packaging from a validated source. It must not be used to disguise unvalidated module work as a release.

## 22. Current Human-Confirmation Items

As of 2026-05-13, the current human-confirmation items include:

- Remote push remains blocked or unperformed unless credentials and explicit push authorization are provided.
- Tracked historical logs and legacy demo runtime logs require a separate cleanup decision before deletion, untracking, or migration.
- Large legacy snapshots and archive materials require separate archive / slimming approval before removal.
- Real Bioinformatics executors require explicit executor-gate confirmation.
- Real Meta statistics executor changes require explicit statistics-gate confirmation.
- External network, database retrieval, external model, or download enablement requires explicit confirmation.
- Any storage of raw prompt, raw response, sensitive source text, credentials, patient-level data, PDFs, downloaded datasets, or full text requires explicit privacy review.

## 23. Current Next-Stage Development Priorities

As of 2026-05-13, the current development priorities are:

1. Keep MainLine stable, testable, and synchronized with the desktop shell and shared UI governance.
2. Continue Bioinformatics user-testable entry consolidation without mixing in PubMed literature workflows.
3. Continue Meta M4 and later literature workflow work without mixing in GEO / TCGA / GTEx expression analysis.
4. Continue Vocabulary hardening for shared query intelligence and context isolation.
5. Build LabTools as a separate module for laboratory calculators, unit conversion, formula lookup, and future image analysis tools.
6. Keep AI Gateway disabled by default while strengthening local model status, privacy gates, redacted audit, and task isolation.
7. Use Integration for staged merge validation.
8. Use ReleaseBuild only for validated internal test packaging and packaged smoke tests.

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
