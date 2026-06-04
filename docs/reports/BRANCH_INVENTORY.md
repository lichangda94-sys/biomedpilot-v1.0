# Branch Inventory

Date: 2026-06-04

Workspace: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

Current branch: `dev/bioinformatics`

Current HEAD: `ccf7967609a283cddfbb83bdf6d68ceb7bc12b63`

Current subject: `add docking lite worker contract`

## Audit Boundary

Phase 2.5 is read-only branch and legacy inventory. No old branch was checked out, merged, cherry-picked, or used to replace the current UI or analysis implementation. The current UI remains the only mainline. Old branches and legacy directories are material libraries only.

This audit did not run validation suites. Tests would validate the current checkout, not prove old branch runtime availability. Old-branch evidence below is therefore classified as inventory evidence unless explicitly marked as current-line proof.

## Guidance Read

| Document | Rule applied |
| --- | --- |
| `../CODEX_UI_BRANCH_MIGRATION_GUIDE.md` | Current UI is the only mainline; old branches are source material only; migrate one page/button/feature at a time after audit. |
| `../CODEX_MINIMAL_REAL_LOOP_SELF_CHECK.md` | Mock, placeholder, static, and testing-level output must not be promoted to real completed analysis. |

## Preserved Worktree State

The worktree contained pre-existing non-Phase-2.5 changes. They were not modified or included as migration work:

```text
 M analysis/modules/molecular_dynamics/module.json
 M analysis/registry/analysis_modules.json
 M analysis/runners/run_module.R
 M tests/test_analysis_runtime_task_bridge.py
 M tests/test_r_analysis_architecture_contract.py
?? analysis/fixtures/inputs/molecular_dynamics/lite_coordinates.gro
?? analysis/fixtures/inputs/molecular_dynamics/lite_mdp.mdp
?? analysis/fixtures/inputs/molecular_dynamics/lite_topology.top
?? analysis/fixtures/inputs/molecular_dynamics/module_input_lite.json
?? docs/bioinformatics/Bioinformatics_handoff_report_20260513.md
?? project_storage/bioinformatics/
```

## Commands Used

| Command | Purpose |
| --- | --- |
| `git status --short` | Capture dirty worktree and preserve unrelated changes. |
| `git branch --show-current` | Capture active branch. |
| `git rev-parse HEAD` | Capture active commit. |
| `git branch --all --verbose --no-abbrev` | Enumerate available refs and linked worktree markers. |
| `git for-each-ref --format='%(refname:short)\|%(objectname:short)\|%(committerdate:short)\|%(subject)' --sort=refname refs/heads` | Capture branch heads and subjects. |
| `git log --oneline --decorate --max-count=60 -- app/bioinformatics app/meta_analysis app/analysis_runtime analysis tests/bioinformatics tests/meta_analysis tests/ui docs/reports scripts` | Review current-line feature history. |
| `git diff --name-only HEAD..<branch> -- app/bioinformatics app/meta_analysis app/analysis_runtime analysis tests/bioinformatics tests/meta_analysis tests/ui docs/reports docs/bioinformatics docs/ui scripts` | Estimate branch divergence without checkout or merge. |
| `git diff --name-status HEAD..<branch> -- ...` | Sample high-relevance branch deltas. |
| `find app/bioinformatics/legacy app/meta_analysis/legacy archive/legacy_sources -maxdepth 4 -type f` | Inventory legacy and archive source files. |
| `find app/bioinformatics app/meta_analysis app/analysis_runtime analysis tests/bioinformatics tests/meta_analysis tests/ui -maxdepth 3 -type f` | Inventory current implementation and tests. |
| `rg -n "QPushButton\|setText\|plot\|report\|DEG\|ORA\|GSEA\|survival\|Cox\|Meta" app/bioinformatics app/meta_analysis -g '*.py'` | Sample current and legacy UI/action surfaces. |

## Current-Line Recent History

Recent current-line commits show current Bio/Meta L3 proof work followed by standard analysis runtime scaffolding and external-tool lite contracts:

```text
ccf7967 add docking lite worker contract
c35ffc9 centralize external R command boundary
13132c3 docs: audit branch inventory migration candidates
a471a25 harden standard package provenance gate
c5bcfa5 label standard package worker boundaries
b5aff58 harden analysis resource lock validation
083e7fe docs: refresh Phase 2.5 branch inventory audit
9436f03 separate standard R worker parameter provenance hash
02f9acb add DEG lite standard worker fixture
6c059ef add DEG standard analysis module contract
6bdc6e2 add multifactor DEG standard result package sidecar
0aa6793 add enrichment standard result package sidecar
bf92811 add standard R analysis worker bridge
5f6150a feat(meta): prove current UI L3 result loop
5c435a8 unify Meta analysis result contract
8036e50 prove Bioinformatics formal DEG L3 UI loop
```

Current standard worker/mock/lite contracts are current code, but they are not evidence of full production analysis unless a selected module has a proven current UI loop and real output contract.

## Local Branch Inventory

| Branch | HEAD | Date | Subject | Bio/Meta/UI relevance | Audit disposition |
| --- | --- | --- | --- | --- | --- |
| `dev/bioinformatics` | `ccf7967` | 2026-06-04 | add docking lite worker contract | Current source of truth for this worktree | Source of truth |
| `dev/release-internal-test` | `6658c3a` | 2026-05-29 | fix(bio): close ReleaseBuild enrichment production gate | High-value Bio ReleaseBuild candidate with R DEG, enrichment, survival/risk, renderer/report history | Candidate library only |
| `codex/releasebuild-formal-deg-carryover` | `a8adc29` | 2026-05-27 | refresh ReleaseBuild analysis internal test gate | Formal DEG/ReleaseBuild gate material | Candidate library only |
| `codex/mainline-survival-clinical-carryover` | `74775fe` | 2026-05-28 | docs(bio): document MainLine enrichment convergence | Survival/clinical and enrichment convergence material | Candidate library only |
| `stable/mainline` | `be8c924` | 2026-05-21 | carry over Bioinformatics formal DEG MVP to MainLine | Older MainLine formal DEG baseline | Historical baseline only |
| `feature/meta-l3-ui-loop` | `5f6150a` | 2026-05-29 | feat(meta): prove current UI L3 result loop | Focused Meta UI proof, already represented in current history | Reference |
| `dev/meta-analysis` | `3aad58a` | 2026-05-18 | Handle LaunchServices psn arguments | Meta OCR/fulltext/package history | Reference only |
| `integration/phase4-meta-l3-scoped-pick` | `3771eb3` | 2026-05-29 | feat(meta): scope Phase 4 L3 UI proof into integration | Meta L3 integration receive branch | Reference |
| `mainline/phase4-meta-l3-scoped-pick` | `41e02bb` | 2026-05-29 | docs(project-control): add constitution v2 for UI baseline governance | MainLine Meta governance | Reference |
| `dev/ui-shell` | `6d5dca5` | 2026-06-01 | docs(project-control): add high fidelity UI integration handoff | UI shell/design/material branch | Design reference only |
| `integration/release-ui-shell-scoped-migration` | `610cc20` | 2026-05-31 | feat(ui): restore scoped UI shell baseline | UI shell baseline and screenshots | UI design reference only |
| `integration/release-labtools-c1-module-nav` | `ef526dc` | 2026-06-01 | feat(ui): gate bio report exports | Cross-module UI shell gates and LabTools material | UI reference only |
| `integration/release-bio-c1-ui-shell` | `dee35e5` | 2026-06-04 | fix(labtools): integrate gated cell imagej macros | LabTools/UI shell integration | Out of Bio/Meta analysis migration scope |
| `dev/labtools` | `c418eba` | 2026-06-04 | Fix gated cell ImageJ macro integration scope | LabTools feature work | Out of Bio/Meta scope |
| `dev/integration` | `056a1f3` | 2026-05-29 | docs(integration): add Phase 4 scoped integration audit | Integration audit branch | Reference |
| `audit/integration-bioinformatics-merge-plan` | `d6a5914` | 2026-05-29 | docs(integration): add bioinformatics merge plan audit | Integration merge planning audit | Reference |
| `audit/mainline-phase4-meta-l3-scope-plan` | `be8c924` | 2026-05-21 | carry over Bioinformatics formal DEG MVP to MainLine | MainLine baseline pointer | Historical |
| `codex/bio-geo-real-download-test` | `a90a2a1` | 2026-05-06 | feat(bio): harden GEO asset recognition and DEG runner | Older GEO recognition/download/DEG runner hardening | Adapter/reference only |
| `codex/stage-3.6-deg-preflight` | `750f076` | 2026-05-12 | feat(bioinformatics): add DEG executor preflight | Pre-B8 DEG preflight | Superseded |
| Bio search UI branches | various | 2026-05 | GEO search UI refinements | Search wording/download UI references | Reference only |
| `codex/bioinformatics-safe-stage2` | `75fe3c3` | 2026-04-30 | feat(bio): add Chinese project wizard UI | Early Bio project wizard | UI material only |
| `codex/meta-workflow-ui` | `8b6d0b6` | 2026-05-10 | feat(meta): connect workflow ui later stages | Early Meta workflow UI | Superseded/reference only |
| `codex/meta-analysis-refresh` | `e9c17c2` | 2026-05-11 | Refine Meta project home UI | Old Meta home UI refinements | UI reference only |
| `codex/meta-search-ui-main` | `b026f9d` | 2026-05-04 | feat(meta): execute confirmed PubMed search | Older PubMed execution branch | Current services supersede |
| Shared vocabulary branches | various | 2026-05 | Medical vocabulary resources | Search/query resource material | Resource reference only |
| AI gateway branches | various | 2026-05 | AI gateway/governance | AI draft routing context | Out of analysis migration scope unless AI is selected |

## High-Relevance Delta Size

Selected branch deltas are large. Direct carry-over is unsafe because many branches would delete or reshape current `analysis/**` and `app/analysis_runtime/**` scaffolds.

| Branch | Files changed vs current in audited paths | Practical implication |
| --- | ---: | --- |
| `dev/release-internal-test` | 2097 | Whole-branch merge would delete/rewrite current standard runtime scaffolds and reshape Bio modules. |
| `codex/releasebuild-formal-deg-carryover` | 1072 | Useful formal DEG gate material, but older and layout-divergent. |
| `codex/mainline-survival-clinical-carryover` | 711 | Useful survival/clinical history, but older than current runtime work. |
| `stable/mainline` | 773 | Historical formal DEG baseline, not current source. |
| `feature/meta-l3-ui-loop` | 126 | Focused Meta L3 proof, already represented in current line. |
| `dev/meta-analysis` | 592 | OCR/fulltext/package material, not current-proven. |
| `dev/ui-shell` | 2103 | UI design/shell material only; diff warns rename detection skipped. |
| `integration/release-ui-shell-scoped-migration` | 776 | UI shell reference, not analysis proof. |
| `codex/bio-geo-real-download-test` | 554 | Early GEO material; current recognition/resolver contracts supersede it. |
| `codex/stage-3.6-deg-preflight` | 1063 | Pre-contract DEG preflight; superseded. |
| `codex/meta-workflow-ui` | 490 | Older Meta UI; use as design reference only. |
| `codex/meta-search-ui-main` | 577 | Older PubMed execution branch; current Meta search services supersede it. |

## Audit Conclusion

The repository contains substantial historical UI, Bioinformatics, Meta Analysis, plot, report, export, test, and helper material. No old branch is safe to merge wholesale. Candidate functionality must be selected one at a time, mapped to a current UI entry, adapted or rewritten against current contracts, and then proven with current tests and real output evidence.

Mock, placeholder, testing-level, branch-only, and legacy-only outputs remain excluded from completed-feature claims.

## Stop Point

This document is inventory output only. It does not authorize branch merge, cherry-pick, UI replacement, analysis algorithm modification, or legacy runtime migration.
