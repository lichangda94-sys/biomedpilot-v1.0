# Branch Inventory

Date: 2026-06-04

Workspace: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

Current branch: `dev/bioinformatics`

Current HEAD: `b77805c242d4f1a47a4cca20fcf21fb3ac4c6e15`

## Audit Boundary

This is Phase 2.5 audit-only work. No legacy branch was checked out, merged, cherry-picked, or used to modify the current UI or analysis algorithms. The current UI remains the only mainline. Old branches, `legacy/` directories, and `archive/legacy_sources/**` are treated only as material libraries.

Current unrelated worktree state was preserved and was not included as a migration action:

```text
 M analysis/modules/univariate/module.json
 M analysis/registry/analysis_modules.json
 M analysis/runners/run_module.R
 M docs/ARCHITECTURE_AUDIT_R_ANALYSIS.md
 M docs/R_ANALYSIS_ARCHITECTURE.md
 M tests/test_analysis_runtime_task_bridge.py
 M tests/test_r_analysis_architecture_contract.py
?? analysis/fixtures/inputs/univariate/lite_clinical.tsv
?? analysis/fixtures/inputs/univariate/module_input_lite.json
?? docs/bioinformatics/Bioinformatics_handoff_report_20260513.md
?? project_storage/bioinformatics/
```

These R analysis worker / univariate lite fixture changes existed before this Phase 2.5 audit refresh and were not treated as migration evidence, completion evidence, or Phase 2.5 implementation work.

## 2026-06-04 Refresh Notes

This refresh re-ran read-only branch and legacy inventory commands against current `dev/bioinformatics` at `b77805c`. Since the prior Phase 2.5 report, the current branch has added analysis runtime isolation scaffolds and mock/lite standard package worker material:

```text
5c835b1 add analysis environment isolation scaffolds
6afb3ff add per-module analysis mock result fixtures
15f6fdd harden standard R analysis runner contract
bf92811 add standard R analysis worker bridge
fb200be add analysis resource governance gate
514d226 expose standard analysis package catalog
5425eb3 add enrichment lite standard worker fixture
b77805c add survival lite standard worker fixture
```

These commits are current-branch material, not old-branch migration. They should be cataloged as `mock/lite standard package scaffold` until a specific module proves full current UI -> task -> real analysis -> result package closure.

Branch inventory still shows no safe whole-branch merge path. The most migration-relevant historical sources remain:

- Bioinformatics ReleaseBuild / internal-test branches for R DEG, enrichment package layout, plot/report renderer gates, risk/report gate history.
- MainLine / survival clinical carry-over branches for survival/clinical contract convergence history.
- Meta L3 branches for current Meta result contract and current UI proof history.
- UI shell branches for design references only.
- `app/bioinformatics/legacy/**`, `app/meta_analysis/legacy/**`, and `archive/legacy_sources/**` as quarantined legacy material.

## Commands Used

| Command | Purpose |
| --- | --- |
| `git status --short && git branch --show-current && git rev-parse HEAD` | Baseline current worktree and HEAD. |
| `git branch --all --format='%(refname:short)'` | Enumerate all local and remote refs available in this worktree. |
| `git branch --format='%(refname:short)\|%(objectname:short)\|%(committerdate:short)\|%(subject)' --sort=refname` | Capture local branch tips and subjects. |
| `git log --oneline --decorate --max-count=30 -- app/bioinformatics app/meta_analysis tests/bioinformatics tests/meta_analysis tests/ui docs/reports scripts app/analysis_runtime analysis` | Capture current-line recent feature history. |
| `git ls-tree -r --name-only <branch> -- app/bioinformatics app/meta_analysis tests/bioinformatics tests/meta_analysis tests/ui docs scripts` | Read-only branch file inventory for high-relevance branches. |
| `find app/bioinformatics/legacy app/meta_analysis/legacy archive archive/legacy_sources -maxdepth 3 -type f` | Legacy directory inventory. |
| `find app/bioinformatics app/meta_analysis tests/bioinformatics tests/meta_analysis tests/ui -path '*/__pycache__' -prune -o -type f -print` | Current active source and test inventory. |
| `rg -n "QPushButton\|report\|plot\|DEG\|ORA\|GSEA\|survival\|Cox\|Meta" app/bioinformatics app/meta_analysis -g '*.py'` | UI/action text and analysis surface sampling. |

## Local Branch Inventory

| Branch | HEAD | Date | Subject | Bio/Meta/UI relevance | Audit disposition |
| --- | --- | --- | --- | --- | --- |
| `dev/bioinformatics` | `b77805c` | 2026-06-04 | add survival lite standard worker fixture | Current source of truth for this worktree; contains Bio and Meta current services plus analysis runtime mock/lite scaffold | Source of truth; current dirty univariate lite scaffold not audited as completion |
| `feature/meta-l3-ui-loop` | `5f6150a` | 2026-05-29 | feat(meta): prove current UI L3 result loop | Meta Phase 4 focused UI L3 proof branch, now largely reachable from current history | Reference; current branch already contains related commits |
| `dev/release-internal-test` | `6658c3a` | 2026-05-29 | fix(bio): close ReleaseBuild enrichment production gate | High Bio ReleaseBuild candidate: structured R DEG, enrichment, GSEA, survival, risk, reports, renderer policy | Candidate library only; no wholesale carry-over |
| `stable/mainline` | `be8c924` | 2026-05-21 | carry over Bioinformatics formal DEG MVP to MainLine | Older MainLine formal DEG baseline | Historical baseline; superseded by current Bio history |
| `dev/meta-analysis` | `3aad58a` | 2026-05-18 | Handle LaunchServices psn arguments | Meta OCR/fulltext/package history, older desktop packaging fixes | Reference only; current Meta UI is source of truth |
| `dev/integration` | `056a1f3` | 2026-05-29 | docs(integration): add Phase 4 scoped integration audit | Integration scoped audit branch | Reference only |
| `dev/ui-shell` | `6d5dca5` | 2026-06-01 | docs(project-control): add high fidelity UI integration handoff | UI shell, screenshots, icon production, result/report export shell material | UI design reference only; not analysis capability |
| `dev/labtools` | `0bd04b2` | 2026-06-04 | Add cell image ImageJ workflows | LabTools feature work | Out of Bio/Meta migration scope |
| `dev/shared-vocabulary` | `b0b938d` | 2026-05-20 | docs(medical-terms): close governance phase | Shared vocabulary resources | Resource reference only |
| `dev/ai-gateway` | `c9a1acc` | 2026-05-14 | docs(ai): align local model ux boundaries | Shared AI routing | Out of analysis migration scope unless AI surfaces are reopened |
| `mainline/phase4-meta-l3-scoped-pick` | `41e02bb` | 2026-05-29 | docs(project-control): add constitution v2 for UI baseline governance | MainLine scoped Meta L3 governance | Reference only |
| `integration/phase4-meta-l3-scoped-pick` | `3771eb3` | 2026-05-29 | feat(meta): scope Phase 4 L3 UI proof into integration | Integration receive branch for Meta Phase 4 | Reference only |
| `integration/release-bio-c1-ui-shell` | `c5728d3` | 2026-06-03 | fix(release): close stage AD wiring gaps | Release UI shell wiring | UI reference only, not analysis migration |
| `integration/release-labtools-c1-module-nav` | `ef526dc` | 2026-06-01 | feat(ui): gate bio report exports | Cross-module UI gate material | UI reference; must not replace current UI |
| `integration/release-ui-shell-scoped-migration` | `610cc20` | 2026-05-31 | feat(ui): restore scoped UI shell baseline | UI shell baseline and icon/status surfaces | UI design reference only |
| `integration/software-remediation-control` | `ec3f274` | 2026-05-31 | docs(project-control): sync UI shell migration evidence | Governance/control docs | Reference only |
| `audit/integration-bioinformatics-merge-plan` | `d6a5914` | 2026-05-29 | docs(integration): add bioinformatics merge plan audit | Audit branch for integration merge planning | Reference only |
| `audit/mainline-phase4-meta-l3-scope-plan` | `be8c924` | 2026-05-21 | carry over Bioinformatics formal DEG MVP to MainLine | Audit pointer to MainLine baseline | Historical |
| `codex/releasebuild-formal-deg-carryover` | `a8adc29` | 2026-05-27 | refresh ReleaseBuild analysis internal test gate | High Bio candidate: DEG/risk/report gates and ReleaseBuild test gate history | Candidate library only |
| `codex/mainline-survival-clinical-carryover` | `74775fe` | 2026-05-28 | docs(bio): document MainLine enrichment convergence | Bio survival/enrichment convergence docs and files | Candidate library only |
| `codex/meta-workflow-ui` | `8b6d0b6` | 2026-05-10 | feat(meta): connect workflow ui later stages | Old Meta workflow UI | Mostly superseded; UI reference only |
| `codex/meta-analysis-refresh` | `e9c17c2` | 2026-05-11 | Refine Meta project home UI | Old Meta project home/UI refinements | UI reference only |
| `codex/meta-search-ui-main` | `b026f9d` | 2026-05-04 | feat(meta): execute confirmed PubMed search | Older PubMed search execution | Current Meta search services supersede it |
| `codex/bio-geo-real-download-test` | `a90a2a1` | 2026-05-06 | feat(bio): harden GEO asset recognition and DEG runner | Older GEO download/recognition/DEG runner hardening | Adapter/reference only; pre-current contracts |
| `codex/stage-3.6-deg-preflight` | `750f076` | 2026-05-12 | feat(bioinformatics): add DEG executor preflight | Old DEG preflight path | Superseded by current B8/B9+ gates |
| `codex/bio-search-ui-main` | `26a33be` | 2026-05-10 | fix(bio): simplify GEO Chinese summary panel | Older Bio GEO search UI | Reference only |
| `codex/bio-ui-download-integration` | `db9ad70` | 2026-05-10 | fix(bio): simplify GEO Chinese summary panel | Older Bio/Meta search/download integration | Reference only |
| `codex/bio-search-ui-integrate-main` | `9bfc88b` | 2026-05-03 | feat(bio): improve GEO disease-aware search UI | Older Bio search UI | Reference only |
| `codex/bio-search-ui-main-legacy` | `65f1be9` | 2026-05-03 | feat(bio): improve GEO disease-aware search UI | Older Bio search UI | Reference only |
| `codex/bioinformatics-safe-stage2` | `75fe3c3` | 2026-04-30 | feat(bio): add Chinese project wizard UI | Early Bio wizard UI | UI material only |
| `codex/biomedpilot-root` | `5e0627f` | 2026-04-30 | feat(meta-ui): add chinese analysis reporting UI | Early root UI | UI material only |
| `codex/bio-chinese-dataset-search-page` | `dcb07cc` | 2026-05-06 | feat(meta): add pico workspace v2 | Mixed early search/UI branch | Reference only |
| `codex/integration-meta-ocr-labtools-carryover` | `8d83bb6` | 2026-05-18 | feat(bioinformatics): route AI drafts through role-based gateway | Integration/OCR/AI gateway context | Reference only |
| `codex/integration-labtools-ui-c2-carryover` | `9d4edf3` | 2026-05-29 | Wire release UI gate buttons | LabTools/UI gate branch | Out of Bio/Meta analysis migration scope |
| `codex/meta-search-main`, `codex/meta-search-main-v2`, `codex/medical-vocabulary-main`, `codex/migrate-medical-vocabulary-stage2`, `codex/shared-vocabulary-refresh`, `codex/vocab-line-stabilization` | various | 2026-05-03 to 2026-05-11 | shared vocabulary commits | Shared terminology resources | Ignore for Phase 2.5 analysis feature migration |
| `codex/merge-latest-app-content`, `codex/restore-ui01-login-baseline`, `codex/ai-gateway-call-isolation-audit`, `codex/ai-gateway-ollama-provider` | various | 2026-05-03 to 2026-05-10 | app shell / AI / consolidation commits | Low direct Bio/Meta analysis relevance | Ignore unless shell/AI work is selected |

## High-Relevance Branch Findings

| Branch | Files/areas observed | Developed material observed | Current availability | Main risk |
| --- | --- | --- | --- | --- |
| `dev/bioinformatics` | `app/bioinformatics/deg_engine/**`, flat `enrichment_*`, `survival_clinical/**`, `plots/**`, `reports/**`, `app/meta_analysis/services/**`, `analysis_runtime/**` | Current Bio DEG/enrichment/survival/report/plot code, current Meta result contract bridge, and a new mock-only analysis runtime bridge | Current source of truth; dirty analysis scaffold must not be treated as completed architecture | Current branch includes mock/runtime scaffold that is not full analysis execution |
| `feature/meta-l3-ui-loop` | `app/meta_analysis/pages/analysis_page.py`, `tests/ui/test_meta_analysis_l3_loop.py`, `docs/reports/META_L3_*` | Focused Meta current UI single-point L3 proof | Already represented by current recent history | Must not be generalized to full Meta production readiness |
| `dev/release-internal-test` | packaged `enrichment/**`, `gsea/**`, R DEG adapters, `plots/real_svg.py`, report renderer policy, survival/risk modules | Rich Bio ReleaseBuild candidate material across DEG, ORA/GSEA, KM/Cox, risk, plots, reports, renderer gates | Not current UI source of truth; current branch has different flat/module layout | Direct merge would overwrite current contracts and possibly elevate testing/report gates |
| `codex/releasebuild-formal-deg-carryover` | R DEG adapters, risk score, calibration/DCA, report-ready, ReleaseBuild gate script | Risk/nomogram and ReleaseBuild gate history | Branch evidence only for several clinical/risk pieces | Clinical overclaim and ReleaseBuild-state dependency |
| `codex/mainline-survival-clinical-carryover` | enrichment/survival convergence docs and files | ORA/GSEA and survival convergence material | Candidate only | Needs adapter to current flat modules and current UI |
| `dev/meta-analysis` | OCR workers, PaddleOCR subprocess runner, fulltext services, package/LaunchServices fixes | Meta OCR/fulltext/package history | Current Meta has fulltext services; OCR branch evidence is not current-proven | External dependency and packaging divergence |
| `dev/ui-shell` and `integration/release-ui-shell-scoped-migration` | UI shell docs, screenshots, icon production, result/report export shell | Design/system UI material | UI reference only | Replacing current UI would violate Phase 2.5 |

## Remote Branches

`git branch --all` in this worktree listed local refs only. No remote branch refs were available for this audit.

## Audit Conclusion

The repository contains substantial historical implementations for UI, Bioinformatics, Meta Analysis, plots, reports, exports, tests, and helper functions. No old branch is safe to merge wholesale. The only safe next step after this audit is selecting one candidate feature and one current UI path, then adapting or rewriting against the current contracts with focused tests.
