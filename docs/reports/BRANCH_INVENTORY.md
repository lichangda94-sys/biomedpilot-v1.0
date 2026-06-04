# Branch Inventory

Date: 2026-06-04

Workspace: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

Current branch: `dev/bioinformatics`

Current HEAD: `a471a25a9153b23c224ea7a96e425c44de92ee5e`

## Audit Boundary

Phase 2.5 is audit-only. No old branch was checked out, merged, cherry-picked, or used to replace current UI or analysis code. The current UI remains the only mainline. Old branches and `legacy/` directories are material libraries only.

The worktree had pre-existing unrelated changes before this audit. They were preserved and are not part of the branch inventory outputs:

```text
 M app/analysis_runtime/__init__.py
 M app/analysis_runtime/r_worker.py
 M app/bioinformatics/deg_engine/multifactor_r_runner.py
 M app/bioinformatics/enrichment_r_adapter.py
 M docs/ARCHITECTURE_AUDIT_R_ANALYSIS.md
 M docs/R_ANALYSIS_ARCHITECTURE.md
 M docs/R_ANALYSIS_REMEDIATION_PLAN.md
 M tests/test_analysis_runtime_task_bridge.py
 M tests/test_r_analysis_architecture_contract.py
?? docs/bioinformatics/Bioinformatics_handoff_report_20260513.md
?? project_storage/bioinformatics/
```

## Guidance Read

| Document | Applied rule |
| --- | --- |
| `../CODEX_UI_BRANCH_MIGRATION_GUIDE.md` | Current UI is the sole mainline; old branches are source material only; no direct merge or replacement. |
| `../CODEX_MINIMAL_REAL_LOOP_SELF_CHECK.md` | Mock/placeholder/testing-level output must not be promoted to completed real analysis. |

## Commands Used

| Command | Purpose |
| --- | --- |
| `git status --short --branch` | Baseline current worktree state. |
| `git branch --all --verbose --no-abbrev` | Enumerate available branch refs and worktree markers. |
| `git for-each-ref --format='%(refname:short)\|%(objectname:short)\|%(committerdate:short)\|%(subject)' --sort=refname refs/heads refs/remotes` | Capture branch tips and subjects. |
| `git rev-parse HEAD` | Capture current HEAD. |
| `git log --oneline --decorate --max-count=45 -- app/bioinformatics app/meta_analysis tests/bioinformatics tests/meta_analysis tests/ui docs/reports scripts app/analysis_runtime analysis` | Capture current-line feature history. |
| `git diff --name-status HEAD..<branch> -- app/bioinformatics app/meta_analysis tests/bioinformatics tests/meta_analysis tests/ui docs/bioinformatics docs/reports docs/ui scripts app/analysis_runtime analysis` | Read-only delta scan for selected high-relevance branches. |
| `find app/bioinformatics/legacy app/meta_analysis/legacy -maxdepth 4 -type f` | Inventory legacy files. |
| `find app/bioinformatics app/meta_analysis app/analysis_runtime analysis tests/bioinformatics tests/meta_analysis tests/ui -maxdepth 4 -type f` | Inventory current feature surfaces. |
| `rg -n "QPushButton\|run\|export\|plot\|report\|DEG\|GSEA\|ORA\|survival\|Cox\|forest\|funnel" app/bioinformatics app/meta_analysis tests/ui` | Map UI/test-visible actions and outputs. |

No functional validation suite was run because this task is a read-only branch/legacy inventory. Running tests would not prove old-branch runtime availability.

## Current-Line Recent History

Recent current-branch commits show two active streams: current Bio/Meta L3 proof work and later standard analysis worker scaffolding. The latter is not a production claim by itself.

```text
a471a25 harden standard package provenance gate
c5bcfa5 label standard package worker boundaries
b5aff58 harden analysis resource lock validation
083e7fe docs: refresh Phase 2.5 branch inventory audit
9436f03 separate standard R worker parameter provenance hash
02f9acb add DEG lite standard worker fixture
6c059ef add DEG standard analysis module contract
6bdc6e2 add multifactor DEG standard result package sidecar
0aa6793 add enrichment standard result package sidecar
8a78a59 add immune infiltration lite standard worker fixture
51b6c31 add multivariate lite standard worker fixture
1d801d2 add univariate lite standard worker fixture
b77805c add survival lite standard worker fixture
5425eb3 add enrichment lite standard worker fixture
514d226 expose standard analysis package catalog
fb200be add analysis resource governance gate
bf92811 add standard R analysis worker bridge
5f6150a feat(meta): prove current UI L3 result loop
5c435a8 unify Meta analysis result contract
8036e50 prove Bioinformatics formal DEG L3 UI loop
```

## Local Branch Inventory

`git branch --all` listed local refs only; no remote refs were available in this worktree.

| Branch | HEAD | Date | Subject | Bio/Meta/UI relevance | Audit disposition |
| --- | --- | --- | --- | --- | --- |
| `dev/bioinformatics` | `a471a25` | 2026-06-04 | harden standard package provenance gate | Current source of truth for this worktree | Source of truth |
| `dev/release-internal-test` | `6658c3a` | 2026-05-29 | fix(bio): close ReleaseBuild enrichment production gate | High-value Bio ReleaseBuild candidate with R DEG, ORA/GSEA, survival/risk, renderer/report history | Candidate library only |
| `codex/releasebuild-formal-deg-carryover` | `a8adc29` | 2026-05-27 | refresh ReleaseBuild analysis internal test gate | DEG/risk/report/ReleaseBuild gate material | Candidate library only |
| `codex/mainline-survival-clinical-carryover` | `74775fe` | 2026-05-28 | docs(bio): document MainLine enrichment convergence | Survival/clinical and enrichment convergence material | Candidate library only |
| `stable/mainline` | `be8c924` | 2026-05-21 | carry over Bioinformatics formal DEG MVP to MainLine | Older MainLine formal DEG baseline | Historical baseline only |
| `feature/meta-l3-ui-loop` | `5f6150a` | 2026-05-29 | feat(meta): prove current UI L3 result loop | Meta focused UI proof; now represented in current history | Reference; not full Meta completion |
| `dev/meta-analysis` | `3aad58a` | 2026-05-18 | Handle LaunchServices psn arguments | Meta OCR/fulltext/package history | Reference only |
| `integration/phase4-meta-l3-scoped-pick` | `3771eb3` | 2026-05-29 | feat(meta): scope Phase 4 L3 UI proof into integration | Integration receive branch for Meta L3 proof | Reference only |
| `mainline/phase4-meta-l3-scoped-pick` | `41e02bb` | 2026-05-29 | docs(project-control): add constitution v2 for UI baseline governance | MainLine Meta governance | Reference only |
| `dev/ui-shell` | `6d5dca5` | 2026-06-01 | docs(project-control): add high fidelity UI integration handoff | UI shell/design/material branch | UI design reference only |
| `integration/release-ui-shell-scoped-migration` | `610cc20` | 2026-05-31 | feat(ui): restore scoped UI shell baseline | UI shell baseline and screenshots | UI design reference only |
| `integration/release-labtools-c1-module-nav` | `ef526dc` | 2026-06-01 | feat(ui): gate bio report exports | Cross-module UI shell gates and LabTools material | UI reference only |
| `integration/release-bio-c1-ui-shell` | `dee35e5` | 2026-06-04 | fix(labtools): integrate gated cell ImageJ macros | LabTools/UI shell integration | Out of Bio/Meta analysis migration scope |
| `dev/labtools` | `c418eba` | 2026-06-04 | Fix gated cell ImageJ macro integration scope | LabTools feature work | Out of Bio/Meta scope |
| `dev/integration` | `056a1f3` | 2026-05-29 | docs(integration): add Phase 4 scoped integration audit | Integration audit branch | Reference only |
| `audit/integration-bioinformatics-merge-plan` | `d6a5914` | 2026-05-29 | docs(integration): add bioinformatics merge plan audit | Integration merge planning audit | Reference only |
| `audit/mainline-phase4-meta-l3-scope-plan` | `be8c924` | 2026-05-21 | carry over Bioinformatics formal DEG MVP to MainLine | MainLine baseline pointer | Historical |
| `codex/bio-geo-real-download-test` | `a90a2a1` | 2026-05-06 | feat(bio): harden GEO asset recognition and DEG runner | Older GEO recognition/download/DEG runner hardening | Adapter/reference only |
| `codex/stage-3.6-deg-preflight` | `750f076` | 2026-05-12 | feat(bioinformatics): add DEG executor preflight | Pre-B8 DEG preflight | Superseded |
| Bio search UI branches | various | 2026-05 | GEO search UI refinements | UI wording/search reference | Reference only |
| `codex/bioinformatics-safe-stage2` | `75fe3c3` | 2026-04-30 | feat(bio): add Chinese project wizard UI | Early Bio project wizard | UI material only |
| `codex/meta-workflow-ui` | `8b6d0b6` | 2026-05-10 | feat(meta): connect workflow ui later stages | Early Meta workflow UI | Superseded/reference only |
| `codex/meta-analysis-refresh` | `e9c17c2` | 2026-05-11 | Refine Meta project home UI | Old Meta home UI refinements | UI reference only |
| `codex/meta-search-ui-main` | `b026f9d` | 2026-05-04 | feat(meta): execute confirmed PubMed search | Older PubMed execution branch | Current services supersede |
| Shared vocabulary branches | various | 2026-05 | Medical vocabulary resources | Search/query resource material | Resource reference only |
| AI gateway branches | various | 2026-05 | AI gateway/governance | AI draft routing context | Out of analysis migration scope unless AI is selected |

## High-Relevance Delta Size

Selected branch deltas were large, confirming that direct branch carry-over is unsafe.

| Branch | Files changed vs current in audited paths | Practical implication |
| --- | ---: | --- |
| `dev/release-internal-test` | 2093 | Whole-branch merge would overwrite/delete current standard runtime scaffolds and reshape Bio modules. |
| `codex/releasebuild-formal-deg-carryover` | 1068 | Useful DEG/ReleaseBuild material, but not layout-compatible wholesale. |
| `codex/mainline-survival-clinical-carryover` | 707 | Useful survival/clinical history, but older than current standard runtime work. |
| `stable/mainline` | 769 | Historical formal DEG baseline, not current source. |
| `feature/meta-l3-ui-loop` | 122 | Focused Meta L3 proof already represented in current line. |
| `dev/meta-analysis` | 588 | OCR/fulltext/package material, not current-proven. |
| `dev/ui-shell` | 2099 | UI design/shell material only; rename detection warning due to large diff. |
| `codex/bio-geo-real-download-test` | 550 | Early GEO material; current recognition/resolver contracts supersede it. |
| `codex/stage-3.6-deg-preflight` | 1059 | Pre-contract DEG preflight; superseded. |
| `codex/meta-workflow-ui` | 486 | Older Meta UI; use as design reference only. |
| `codex/meta-search-ui-main` | 573 | Older PubMed execution branch; current search services supersede it. |

## Audit Conclusion

The repository contains substantial historical UI, Bioinformatics, Meta Analysis, plot, report, export, test, and helper material. No old branch is safe to merge wholesale. The only safe post-audit path is selecting one candidate feature and one current UI entry, then adapting or rewriting against current contracts with focused proof.

Mock, placeholder, testing-level, branch-only, and legacy-only outputs remain excluded from completion claims.

## Stop Point

This document is inventory output only. It does not authorize branch merge, cherry-pick, UI replacement, algorithm modification, or legacy runtime migration.
