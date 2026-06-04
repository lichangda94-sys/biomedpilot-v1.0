# Branch Inventory

Date: 2026-06-04

Workspace: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

Current branch: `dev/bioinformatics`

Current HEAD: `f8590cc458317656aee600430e911d57cecbb32f`

Current subject: `harden standard package module mapping`

## Audit Boundary

Phase 2.5 is a read-only branch, legacy, and historical implementation inventory. No old branch was checked out, merged, cherry-picked, or used to replace the current UI or analysis implementation. The current UI remains the only mainline. Old branches, `legacy/` directories, and `archive/legacy_sources/**` are material libraries only.

This audit does not classify any branch-only, legacy-only, mock, placeholder, dry-run, or testing-level output as a completed current feature. Runtime availability requires a current UI entry, current contract mapping, current tests, and real output evidence.

## Guidance Read

| Document | Rule applied |
| --- | --- |
| `../CODEX_UI_BRANCH_MIGRATION_GUIDE.md` | Current UI is the only mainline; old branches are source material only; migrate one page/button/feature at a time after audit. |
| `../CODEX_MINIMAL_REAL_LOOP_SELF_CHECK.md` | Mock, placeholder, static, branch-only, and testing-level output must not be promoted to real completed analysis. |

## Worktree State

The current worktree was not clean before this refresh. The Phase 2.5 report files were updated; unrelated non-audit changes were observed and left untouched:

```text
 M app/bioinformatics/gene_set_resources.py
 M tests/bioinformatics/test_gene_set_resources.py
?? docs/bioinformatics/Bioinformatics_handoff_report_20260513.md
?? project_storage/bioinformatics/
```

These paths are not Phase 2.5 migration outputs and were not used to claim current runtime availability.

## Commands Used

| Command | Purpose |
| --- | --- |
| `sed -n '1,240p' ../CODEX_UI_BRANCH_MIGRATION_GUIDE.md` | Read branch/UI migration rules. |
| `sed -n '1,240p' ../CODEX_MINIMAL_REAL_LOOP_SELF_CHECK.md` | Read real-loop and testing-level rules. |
| `git status --short --branch` | Capture active worktree and out-of-scope dirty files. |
| `git branch --all --verbose --no-abbrev` | Enumerate available local refs and linked worktree markers. |
| `git for-each-ref --format='%(refname:short)\|%(objectname:short)\|%(committerdate:short)\|%(subject)' --sort=refname refs/heads refs/remotes` | Capture branch heads, dates, and subjects. |
| `git rev-parse HEAD` | Capture current baseline commit. |
| `git log --oneline --decorate --max-count=90 -- app/bioinformatics app/meta_analysis app/analysis_runtime analysis tests/bioinformatics tests/meta_analysis tests/ui docs/reports scripts` | Review current-line Bio/Meta/UI/runtime history. |
| `git diff --name-only HEAD..<branch> -- app/bioinformatics app/meta_analysis app/analysis_runtime analysis tests/bioinformatics tests/meta_analysis tests/ui docs/reports docs/bioinformatics docs/ui scripts` | Estimate high-relevance branch divergence without checkout or merge. |
| `git diff --name-status HEAD..<branch> -- ...` | Sample candidate branch deltas. |
| `find app/bioinformatics/legacy app/meta_analysis/legacy -maxdepth 4 -type f` | Inventory in-tree legacy source files. |
| `find archive -maxdepth 4 -type f` | Inventory archive mirrors. |
| `find app/bioinformatics app/meta_analysis app/analysis_runtime analysis tests/bioinformatics tests/meta_analysis tests/ui -maxdepth 3 -type f` | Inventory current implementation and tests. |
| `rg -n "QPushButton\|setText\|run\|export\|plot\|report\|DEG\|GSEA\|ORA\|survival\|Cox\|forest\|funnel\|meta" app/bioinformatics app/meta_analysis tests/ui -g '*.py'` | Sample current UI/action/test surfaces. |

No functional tests were required for this documentation-only inventory. Tests would validate the current checkout, not prove old branch runtime availability.

## Current-Line Recent History

Recent current-line commits show Meta and Bio single-point L3 proof work followed by standard analysis runtime scaffolding, standard package sidecars, worker invocation manifests, and standard package module mapping:

```text
f8590cc harden standard package module mapping
521907c record survival sidecar worker invocations
cdae468 validate indexed worker invocation artifacts
3ef6618 index legacy sidecar worker invocation logs
5829e79 record legacy analysis sidecar worker invocations
42d82f2 harden direct R worker package contract
8c34c37 validate full-mode analysis environment snapshots
b0b96ac record full-mode analysis environment blockers
fca3a01 mirror correlation results into standard packages
7e07dba mirror immune scoring results into standard packages
7f9b242 mirror formal DEG results into standard packages
05d3afc mirror survival clinical results into standard packages
ec65eb4 expose standard analysis package artifact manifests
cf43487 validate R worker invocation manifest schema
db5bef1 surface R worker invocation diagnostics in catalog
2eb11b6 extend R worker invocation manifest to all task bridge paths
00d7bd6 add R worker invocation manifest contract
239131a add R analysis environment registry contract
bf92811 add standard R analysis worker bridge
5f6150a feat(meta): prove current UI L3 result loop
5c435a8 unify Meta analysis result contract
8036e50 prove Bioinformatics formal DEG L3 UI loop
```

Current standard worker/mock/lite contracts are current code. They are not evidence that every module has full production analysis.

## Local Branch Inventory

| Branch | HEAD | Date | Subject | Bio/Meta/UI relevance | Audit disposition |
| --- | --- | --- | --- | --- | --- |
| `dev/bioinformatics` | `f8590cc` | 2026-06-04 | harden standard package module mapping | Current source of truth for this worktree | Source of truth |
| `dev/release-internal-test` | `6658c3a` | 2026-05-29 | fix(bio): close ReleaseBuild enrichment production gate | High-value Bio candidate with DEG, enrichment, survival/risk, renderer/report history | Candidate library only |
| `codex/releasebuild-formal-deg-carryover` | `a8adc29` | 2026-05-27 | refresh ReleaseBuild analysis internal test gate | Formal DEG and ReleaseBuild gate material | Candidate library only |
| `codex/mainline-survival-clinical-carryover` | `74775fe` | 2026-05-28 | docs(bio): document MainLine enrichment convergence | Survival/clinical and enrichment convergence material | Candidate library only |
| `stable/mainline` | `be8c924` | 2026-05-21 | carry over Bioinformatics formal DEG MVP to MainLine | Older MainLine formal DEG baseline | Historical baseline only |
| `feature/meta-l3-ui-loop` | `5f6150a` | 2026-05-29 | feat(meta): prove current UI L3 result loop | Focused Meta UI proof, already represented in current history | Reference |
| `dev/meta-analysis` | `3aad58a` | 2026-05-18 | Handle LaunchServices psn arguments | Meta OCR/fulltext/package history | Reference only |
| `integration/phase4-meta-l3-scoped-pick` | `3771eb3` | 2026-05-29 | feat(meta): scope Phase 4 L3 UI proof into integration | Meta L3 integration receive branch | Reference |
| `mainline/phase4-meta-l3-scoped-pick` | `41e02bb` | 2026-05-29 | docs(project-control): add constitution v2 for UI baseline governance | MainLine Meta governance | Reference |
| `dev/ui-shell` | `6d5dca5` | 2026-06-01 | docs(project-control): add high fidelity UI integration handoff | UI shell/design/material branch | Design reference only |
| `integration/release-ui-shell-scoped-migration` | `610cc20` | 2026-05-31 | feat(ui): restore scoped UI shell baseline | UI shell baseline and screenshots | UI design reference only |
| `integration/release-labtools-c1-module-nav` | `ef526dc` | 2026-06-01 | feat(ui): gate bio report exports | Cross-module UI shell gates and LabTools material | UI reference only |
| `integration/release-bio-c1-ui-shell` | `f0af1d4` | 2026-06-04 | fix(labtools): scope latest imagej macro extensions | LabTools/UI shell integration | Out of Bio/Meta analysis migration scope |
| `dev/labtools` | `c418eba` | 2026-06-04 | Fix gated cell ImageJ macro integration scope | LabTools feature work | Out of Bio/Meta scope |
| `dev/integration` | `056a1f3` | 2026-05-29 | docs(integration): add Phase 4 scoped integration audit | Integration audit branch | Reference |
| `audit/integration-bioinformatics-merge-plan` | `d6a5914` | 2026-05-29 | docs(integration): add bioinformatics merge plan audit | Integration merge planning audit | Reference |
| `audit/mainline-phase4-meta-l3-scope-plan` | `be8c924` | 2026-05-21 | carry over Bioinformatics formal DEG MVP to MainLine | MainLine baseline pointer | Historical |
| `codex/bio-geo-real-download-test` | `a90a2a1` | 2026-05-06 | feat(bio): harden GEO asset recognition and DEG runner | Older GEO recognition/download/DEG runner hardening | Adapter/reference only |
| `codex/stage-3.6-deg-preflight` | `750f076` | 2026-05-12 | feat(bioinformatics): add DEG executor preflight | Pre-contract DEG preflight | Superseded |
| Bio search UI branches | various | 2026-05 | GEO search UI refinements | Search wording/download UI references | Reference only |
| `codex/bioinformatics-safe-stage2` | `75fe3c3` | 2026-04-30 | feat(bio): add Chinese project wizard UI | Early Bio project wizard | UI material only |
| `codex/meta-workflow-ui` | `8b6d0b6` | 2026-05-10 | feat(meta): connect workflow ui later stages | Early Meta workflow UI | Superseded/reference only |
| `codex/meta-analysis-refresh` | `e9c17c2` | 2026-05-11 | Refine Meta project home UI | Old Meta home UI refinements | UI reference only |
| `codex/meta-search-ui-main` | `b026f9d` | 2026-05-04 | feat(meta): execute confirmed PubMed search | Older PubMed execution branch | Current services supersede |
| Shared vocabulary branches | various | 2026-05 | Medical vocabulary resources | Search/query resource material | Resource reference only |
| AI gateway branches | various | 2026-05 | AI gateway/governance | AI draft routing context | Out of analysis migration scope unless AI is selected |

## High-Relevance Delta Size

Selected branch deltas are large. Direct carry-over is unsafe because several branches would delete or reshape current `analysis/**`, `app/analysis_runtime/**`, current Bio contracts, or current Meta runtime paths.

| Branch | Files changed vs current in audited paths | Practical implication |
| --- | ---: | --- |
| `dev/release-internal-test` | 2118 | Whole-branch merge would delete/rewrite current standard runtime scaffolds and reshape Bio modules. |
| `codex/releasebuild-formal-deg-carryover` | 1093 | Useful formal DEG gate material, but older and layout-divergent. |
| `codex/mainline-survival-clinical-carryover` | 732 | Useful survival/clinical history, but older than current runtime work. |
| `stable/mainline` | 790 | Historical formal DEG baseline, not current source. |
| `feature/meta-l3-ui-loop` | 149 | Focused Meta L3 proof, already represented in current line. |
| `dev/meta-analysis` | 607 | OCR/fulltext/package material, not current-proven. |
| `dev/ui-shell` | 2118 | UI design/shell material only; diff warns direct carry-over is unsafe. |
| `integration/release-ui-shell-scoped-migration` | 793 | UI shell reference, not analysis proof. |
| `integration/release-labtools-c1-module-nav` | 809 | Cross-module shell/report export reference, not analysis proof. |
| `codex/bio-geo-real-download-test` | 567 | Early GEO material; current recognition/resolver contracts supersede it. |
| `codex/stage-3.6-deg-preflight` | 1078 | Pre-contract DEG preflight; superseded. |
| `codex/meta-workflow-ui` | 505 | Older Meta UI; use as design reference only. |
| `codex/meta-search-ui-main` | 590 | Older PubMed execution branch; current Meta search services supersede it. |
| `integration/phase4-meta-l3-scoped-pick` | 930 | Meta L3 receive branch, not a safe whole-branch source. |
| `mainline/phase4-meta-l3-scoped-pick` | 790 | MainLine governance/reference branch, not current runtime proof. |

## Audit Conclusion

The repository contains substantial historical UI, Bioinformatics, Meta Analysis, plot, report, export, test, and helper material. No old branch is safe to merge wholesale. Candidate functionality must be selected one at a time, mapped to a current UI entry, adapted or rewritten against current contracts, and then proven with current tests and real output evidence.

Mock, placeholder, dry-run, testing-level, branch-only, and legacy-only outputs remain excluded from completed-feature claims.

## Stop Point

This document is inventory output only. It does not authorize branch merge, cherry-pick, UI replacement, analysis algorithm modification, or legacy runtime migration.
