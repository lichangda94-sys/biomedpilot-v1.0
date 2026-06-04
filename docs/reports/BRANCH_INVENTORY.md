# Branch Inventory

Date: 2026-06-04

Workspace: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

Current branch: `dev/bioinformatics`

Current HEAD: `0aa6793f460f79a78036c352f918a5acfc7a522b`

## Audit Boundary

This Phase 2.5 inventory is read-only. No legacy branch was checked out, merged, cherry-picked, or used to modify the current UI or analysis algorithms. The current UI remains the only mainline. Old branches, `legacy/` directories, and `archive/legacy_sources/**` are material libraries only.

The worktree had pre-existing unrelated untracked files before this audit and they were preserved:

```text
?? docs/bioinformatics/Bioinformatics_handoff_report_20260513.md
?? project_storage/bioinformatics/
```

## Commands Used

| Command | Purpose |
| --- | --- |
| `git status --short` | Baseline current worktree state. |
| `git branch --all --verbose --no-abbrev` | Enumerate available branch refs and worktree markers. |
| `git for-each-ref --format='%(refname:short)\|%(objectname)\|%(committerdate:short)\|%(subject)' refs/heads refs/remotes` | Capture branch tips and subjects. |
| `git rev-parse HEAD` | Capture current HEAD. |
| `git log --oneline --decorate --max-count=40 -- app/bioinformatics app/meta_analysis tests/bioinformatics tests/meta_analysis tests/ui docs/reports scripts app/analysis_runtime analysis` | Capture current-line feature history. |
| `find analysis -maxdepth 4 -type f` | Inventory current standard analysis runtime scaffolds. |
| `find app/analysis_runtime -maxdepth 3 -type f` | Inventory current runtime bridge files. |
| `find app/bioinformatics -maxdepth 3 -type f ...` | Inventory current Bioinformatics feature surfaces. |
| `find app/meta_analysis -maxdepth 3 -type f ...` | Inventory current Meta Analysis feature surfaces. |
| `git diff --name-status HEAD..<branch> -- app/bioinformatics app/meta_analysis tests/bioinformatics tests/meta_analysis tests/ui docs/bioinformatics docs/reports docs/ui scripts analysis app/analysis_runtime` | Read-only delta scan for selected high-relevance branches. |
| `rg --files \| rg '(^\|/)(legacy\|Legacy\|old\|archive\|deprecated)(/\|$)'` | Inventory legacy/archive paths. |

No validation test suite was run because this task is an audit-only branch and legacy inventory, not implementation.

## Current-Line Recent History

The current branch contains recent standard analysis runtime scaffold work after the earlier Phase 2.5 reports:

```text
0aa6793 add enrichment standard result package sidecar
8a78a59 add immune infiltration lite standard worker fixture
51b6c31 add multivariate lite standard worker fixture
1d801d2 add univariate lite standard worker fixture
8356ba0 docs: refresh branch inventory migration audit
b77805c add survival lite standard worker fixture
5425eb3 add enrichment lite standard worker fixture
514d226 expose standard analysis package catalog
fb200be add analysis resource governance gate
bf92811 add standard R analysis worker bridge
15f6fdd harden standard R analysis runner contract
6afb3ff add per-module analysis mock result fixtures
5c835b1 add analysis environment isolation scaffolds
c7d771c docs: refresh branch inventory migration audit
4e699cf add analysis runtime mock task bridge
98382de audit R analysis worker architecture
```

These commits are current-branch work, not old-branch migration. The standard runtime pieces remain mock/lite/testing-level unless a selected module has a current UI to real engine to package proof.

## Local Branch Inventory

| Branch | HEAD | Date | Subject | Bio/Meta/UI relevance | Audit disposition |
| --- | --- | --- | --- | --- | --- |
| `dev/bioinformatics` | `0aa6793` | 2026-06-04 | add enrichment standard result package sidecar | Current source of truth for this worktree; includes current Bio/Meta modules and analysis runtime scaffolds | Source of truth |
| `dev/release-internal-test` | `6658c3a` | 2026-05-29 | fix(bio): close ReleaseBuild enrichment production gate | High-value Bio ReleaseBuild candidate with R DEG, ORA/GSEA, survival/risk, renderer/report history | Candidate library only |
| `codex/releasebuild-formal-deg-carryover` | `a8adc29` | 2026-05-27 | refresh ReleaseBuild analysis internal test gate | DEG/risk/report/ReleaseBuild gate material | Candidate library only |
| `codex/mainline-survival-clinical-carryover` | `74775fe` | 2026-05-28 | docs(bio): document MainLine enrichment convergence | Survival/clinical and enrichment convergence material | Candidate library only |
| `stable/mainline` | `be8c924` | 2026-05-21 | carry over Bioinformatics formal DEG MVP to MainLine | Older MainLine formal DEG baseline | Historical baseline only |
| `feature/meta-l3-ui-loop` | `5f6150a` | 2026-05-29 | feat(meta): prove current UI L3 result loop | Meta Phase 4 focused UI proof branch, represented by current history | Reference; do not generalize to full Meta |
| `dev/meta-analysis` | `3aad58a` | 2026-05-18 | Handle LaunchServices psn arguments | Meta OCR/fulltext/package history | Reference only; not current-proven |
| `integration/phase4-meta-l3-scoped-pick` | `3771eb3` | 2026-05-29 | feat(meta): scope Phase 4 L3 UI proof into integration | Integration receive branch for Meta L3 proof | Reference only |
| `mainline/phase4-meta-l3-scoped-pick` | `41e02bb` | 2026-05-29 | docs(project-control): add constitution v2 for UI baseline governance | MainLine Meta governance | Reference only |
| `dev/ui-shell` | `6d5dca5` | 2026-06-01 | docs(project-control): add high fidelity UI integration handoff | UI shell/design/material branch | UI design reference only |
| `integration/release-ui-shell-scoped-migration` | `610cc20` | 2026-05-31 | feat(ui): restore scoped UI shell baseline | UI shell baseline and screenshots | UI design reference only |
| `integration/release-labtools-c1-module-nav` | `ef526dc` | 2026-06-01 | feat(ui): gate bio report exports | Cross-module UI shell gates and LabTools material | UI reference only |
| `integration/release-bio-c1-ui-shell` | `6cf4da5` | 2026-06-04 | fix(labtools): enable imagej engine macro preparation | LabTools/UI shell integration work | Out of Bio/Meta analysis migration scope |
| `dev/labtools` | `2fa005d` | 2026-06-04 | Add migration streak ROI ImageJ workflow | LabTools feature work | Out of Bio/Meta scope |
| `dev/integration` | `056a1f3` | 2026-05-29 | docs(integration): add Phase 4 scoped integration audit | Integration audit branch | Reference only |
| `audit/integration-bioinformatics-merge-plan` | `d6a5914` | 2026-05-29 | docs(integration): add bioinformatics merge plan audit | Integration merge planning audit | Reference only |
| `audit/mainline-phase4-meta-l3-scope-plan` | `be8c924` | 2026-05-21 | carry over Bioinformatics formal DEG MVP to MainLine | MainLine baseline pointer | Historical |
| `codex/bio-geo-real-download-test` | `a90a2a1` | 2026-05-06 | feat(bio): harden GEO asset recognition and DEG runner | Older GEO recognition/download/DEG runner hardening | Adapter/reference only |
| `codex/stage-3.6-deg-preflight` | `750f076` | 2026-05-12 | feat(bioinformatics): add DEG executor preflight | Pre-B8 DEG preflight | Superseded |
| `codex/bio-search-ui-main`, `codex/bio-search-ui-main-legacy`, `codex/bio-search-ui-integrate-main`, `codex/bio-ui-download-integration` | various | 2026-05-03 to 2026-05-10 | Bio GEO search UI refinements | UI wording/search reference | Reference only |
| `codex/bioinformatics-safe-stage2` | `75fe3c3` | 2026-04-30 | feat(bio): add Chinese project wizard UI | Early Bio project wizard | UI material only |
| `codex/meta-workflow-ui` | `8b6d0b6` | 2026-05-10 | feat(meta): connect workflow ui later stages | Early Meta workflow UI | Superseded/reference only |
| `codex/meta-analysis-refresh` | `e9c17c2` | 2026-05-11 | Refine Meta project home UI | Old Meta home UI refinements | UI reference only |
| `codex/meta-search-ui-main` | `b026f9d` | 2026-05-04 | feat(meta): execute confirmed PubMed search | Older PubMed execution branch | Current services supersede |
| `codex/bio-chinese-dataset-search-page` | `dcb07cc` | 2026-05-06 | feat(meta): add pico workspace v2 | Mixed early search/UI branch | Reference only |
| `codex/biomedpilot-root` | `5e0627f` | 2026-04-30 | feat(meta-ui): add chinese analysis reporting UI | Early root UI | UI material only |
| `codex/integration-meta-ocr-labtools-carryover` | `8d83bb6` | 2026-05-18 | feat(bioinformatics): route AI drafts through role-based gateway | OCR/AI gateway context | Reference only |
| `codex/integration-labtools-ui-c2-carryover` | `9d4edf3` | 2026-05-29 | Wire release UI gate buttons | LabTools/UI gate branch | Out of Bio/Meta scope |
| `dev/shared-vocabulary`, `codex/meta-search-main`, `codex/meta-search-main-v2`, `codex/medical-vocabulary-main`, `codex/migrate-medical-vocabulary-stage2`, `codex/shared-vocabulary-refresh`, `codex/vocab-line-stabilization` | various | 2026-05-03 to 2026-05-20 | Medical vocabulary resources | Resource reference only |
| `dev/ai-gateway`, `codex/ai-gateway-call-isolation-audit`, `codex/ai-gateway-ollama-provider` | various | 2026-05-10 to 2026-05-14 | AI gateway/governance | Out of analysis migration scope unless AI is selected |
| `codex/merge-latest-app-content`, `codex/restore-ui01-login-baseline` | various | 2026-05-03 | App shell/content restore | Low direct analysis relevance |

`git branch --all` listed local refs only; no remote branch refs were available in this worktree.

## High-Relevance Branch Findings

| Branch/path | Observed files/areas | Developed material | Current availability | Risk |
| --- | --- | --- | --- | --- |
| `dev/bioinformatics` | `app/bioinformatics/**`, `app/meta_analysis/**`, `app/analysis_runtime/**`, `analysis/**`, current tests | Current Bio DEG/enrichment/survival/plot/report modules, current Meta result contract, standard mock/lite runtime scaffolds | Current source of truth | Current scaffolds must not be overstated as production R/Bioc or full L3 |
| `dev/release-internal-test` | structured `app/bioinformatics/enrichment/**`, `gsea/**`, R DEG files, renderer/report policy files | Rich ReleaseBuild material across DEG, ORA/GSEA, plots, reports, survival/risk | Branch-only; current branch uses different flat/module layout in several places | Whole-branch merge would delete/replace current contracts |
| `codex/releasebuild-formal-deg-carryover` | R DEG runtime, risk score, report gates, ReleaseBuild test script history | Formal DEG/risk/report candidate material | Branch-only | Clinical/risk overclaim and ReleaseBuild state coupling |
| `codex/mainline-survival-clinical-carryover` | survival clinical, enrichment convergence docs/files | Survival/clinical and enrichment carry-over history | Candidate only | Needs current contract adapter |
| `dev/meta-analysis` | OCR workers, fulltext services, LaunchServices/package fixes | Meta OCR/fulltext/package material | Branch-only for OCR; current Meta has separate services | External dependency/package divergence |
| `dev/ui-shell` / `integration/*ui*` | `docs/ui/**`, shared UI components, screenshots, report/export shell tests | UI shell and visual design material | Design reference only | UI replacement would violate Phase 2.5 |
| `app/bioinformatics/legacy/**` | old GEO, TCGA/GTEx, literature, scripts, tests | Historical Bio utilities | Legacy only | Old paths bypass current contracts |
| `app/meta_analysis/legacy/**` | old workbench, literature, extraction, reporting, fulltext, task runner | Historical Meta workbench stack | Legacy only | Old shell/task/result contracts |
| `archive/legacy_sources/**` | duplicate Bio and Meta snapshots | File archaeology | Archive only | Duplicate, stale, not executable evidence |

## Audit Conclusion

The repository contains substantial historical UI, Bioinformatics, Meta Analysis, plot, report, export, test, and helper material. No old branch is safe to merge wholesale. The only safe post-audit path is selecting one candidate feature and one current UI entry, then adapting or rewriting against current contracts with focused proof. Mock, placeholder, testing-level, branch-only, and legacy-only outputs remain excluded from completion claims.
