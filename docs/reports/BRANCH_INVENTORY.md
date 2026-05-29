# Branch Inventory

Date: 2026-05-29

Workspace: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

Current branch: `dev/bioinformatics`

Current HEAD: `5c435a8aa75650dded37b7f6ad7da83a9c5e422d`

## Audit Boundary

This is Phase 2.5 audit-only work. No legacy branch was checked out, merged, or cherry-picked. The current UI remains the only mainline. Old branches and `legacy/` directories are treated only as a material library.

Current unrelated untracked files were preserved:

```text
docs/bioinformatics/Bioinformatics_handoff_report_20260513.md
project_storage/bioinformatics/
```

## Commands Used

| Command | Purpose |
| --- | --- |
| `git status --short && git branch --show-current && git rev-parse HEAD` | Baseline current worktree. |
| `git branch --format='%(refname:short)|%(objectname:short)|%(committerdate:short)|%(subject)' --sort=refname` | List local branches and commit subjects. |
| `git branch -r --format='%(refname:short)|%(objectname:short)|%(committerdate:short)|%(subject)' --sort=refname` | Check remote branch inventory; no remote branches were listed. |
| `git diff --name-status HEAD..<branch> -- app/bioinformatics app/meta_analysis tests/bioinformatics tests/meta_analysis tests/ui docs/reports docs/bioinformatics scripts` | Read-only file-difference sampling for relevant branches. |
| `git log --oneline --max-count=8 <branch> -- app/bioinformatics app/meta_analysis tests/bioinformatics tests/meta_analysis tests/ui docs scripts` | Read-only branch commit evidence. |
| `rg --files app | rg '(^|/)legacy(/|_)|legacy'` | Legacy file inventory. |
| `find app/bioinformatics/legacy app/meta_analysis/legacy -maxdepth 2 -type d` | Legacy module directory inventory. |

## Local Branch Inventory

| Branch | HEAD | Date | Subject | Ahead/behind current | Bio/Meta relevance | Audit disposition |
| --- | --- | --- | --- | --- | --- | --- |
| `dev/bioinformatics` | `5c435a8` | 2026-05-29 | unify Meta analysis result contract | `0/0` | Current mainline for this audit | Source of truth |
| `dev/release-internal-test` | `6658c3a` | 2026-05-29 | fix(bio): close ReleaseBuild enrichment production gate | `614/82` | High: ReleaseBuild candidate for Bio DEG/enrichment/report/UI gates | Migration source, not directly usable |
| `stable/mainline` | `be8c924` | 2026-05-21 | carry over Bioinformatics formal DEG MVP to MainLine | `92/65` | High: older MainLine Bio formal DEG carry-over | Historical baseline |
| `dev/meta-analysis` | `3aad58a` | 2026-05-18 | Handle LaunchServices psn arguments | `78/133` | High for Meta OCR/fulltext/package history, but diverges from current Bio tree | Selective reference only |
| `dev/integration` | `ea57a49` | 2026-05-22 | Restore bioinformatics task plan import surface | `338/82` | Medium/high: integration registry and UI rebuild work | Reference for integration contracts |
| `dev/labtools` | `93b79a9` | 2026-05-26 | test(labtools): add simulated LAN interop coverage | `130/133` | Low for Bio/Meta analysis | Ignore for this phase |
| `dev/shared-vocabulary` | `b0b938d` | 2026-05-20 | docs(medical-terms): close governance phase | `96/133` | Low/medium shared vocabulary | Shared material only |
| `dev/ui-shell` | `8a92120` | 2026-05-28 | Simplify about screen copy | `211/133` | Medium UI shell only | UI reference, not analysis migration |
| `dev/ai-gateway` | `c9a1acc` | 2026-05-14 | docs(ai): align local model ux boundaries | `60/133` | Low/medium shared AI routing | Ignore unless AI surfaces are revisited |
| `codex/releasebuild-formal-deg-carryover` | `a8adc29` | 2026-05-27 | refresh ReleaseBuild analysis internal test gate | `431/82` | High Bio candidate branch | Candidate ledger source |
| `codex/mainline-survival-clinical-carryover` | `74775fe` | 2026-05-28 | docs(bio): document MainLine enrichment convergence | `103/65` | High Bio enrichment/survival convergence evidence | Candidate ledger source |
| `codex/meta-workflow-ui` | `8b6d0b6` | 2026-05-10 | feat(meta): connect workflow ui later stages | `1/142` | Medium Meta UI history | Mostly superseded by current Meta pages |
| `codex/meta-analysis-refresh` | `e9c17c2` | 2026-05-11 | Refine Meta project home UI | `43/133` | Medium Meta project home UI | UI reference only |
| `codex/bio-geo-real-download-test` | `a90a2a1` | 2026-05-06 | feat(bio): harden GEO asset recognition and DEG runner | `1/182` | Medium Bio GEO/GSE legacy recognition | Reference only |
| `codex/stage-3.6-deg-preflight` | `750f076` | 2026-05-12 | feat(bioinformatics): add DEG executor preflight | `59/133` | Medium old DEG preflight path | Superseded by current B8/B9 contracts |
| `codex/bio-search-ui-main` | `26a33be` | 2026-05-10 | fix(bio): simplify GEO Chinese summary panel | `30/208` | Medium old GEO search UI | Reference only |
| `codex/bio-ui-download-integration` | `db9ad70` | 2026-05-10 | fix(bio): simplify GEO Chinese summary panel | `0/148` | Medium old Bio/Meta integration | Reference only |
| `codex/bioinformatics-safe-stage2` | `75fe3c3` | 2026-04-30 | feat(bio): add Chinese project wizard UI | `61/275` | Low/medium old Bio wizard | UI material only |
| `codex/biomedpilot-root` | `5e0627f` | 2026-04-30 | feat(meta-ui): add chinese analysis reporting UI | `0/227` | Low/medium old root UI | UI material only |
| `codex/bio-search-ui-integrate-main` | `9bfc88b` | 2026-05-03 | feat(bio): improve GEO disease-aware search UI | `0/223` | Low/medium old Bio search UI | Reference only |
| `codex/bio-search-ui-main-legacy` | `65f1be9` | 2026-05-03 | feat(bio): improve GEO disease-aware search UI | `1/226` | Low/medium old Bio search UI | Reference only |
| `codex/meta-search-ui-main` | `b026f9d` | 2026-05-04 | feat(meta): execute confirmed PubMed search | `2/208` | Medium old PubMed search execution | Current Meta search has newer services |
| `codex/meta-search-main` / `codex/meta-search-main-v2` | `4e0ca45` | 2026-05-03 | feat(shared): migrate medical vocabulary index into BioMedPilot | `0/226` | Low shared vocabulary | Ignore for analysis migration |
| `codex/shared-vocabulary-refresh` | `cfed80e` | 2026-05-11 | feat(shared): add cardiovascular medical vocabulary | `48/133` | Low shared vocabulary | Ignore for this phase |
| `codex/medical-vocabulary-main` | `393b3e8` | 2026-05-03 | feat(shared): expand systematic medical vocabulary coverage | `0/224` | Low shared vocabulary | Ignore for this phase |
| `codex/migrate-medical-vocabulary-stage2` | `4e0ca45` | 2026-05-03 | feat(shared): migrate medical vocabulary index into BioMedPilot | `0/226` | Low shared vocabulary | Ignore for this phase |
| `codex/vocab-line-stabilization` | `b778543` | 2026-05-04 | docs(shared): isolate medical vocabulary worktree | `1/211` | Low shared vocabulary | Ignore for this phase |
| `codex/merge-latest-app-content` | `f87a5f6` | 2026-05-03 | fix(app): keep desktop theme light | `0/221` | Low app shell | Ignore for this phase |
| `codex/restore-ui01-login-baseline` | `ba837a7` | 2026-05-03 | fix(app): include restored runtime dirs in desktop package | `0/219` | Low app shell/package | Ignore for this phase |
| `codex/ai-gateway-call-isolation-audit` | `2fea2a6` | 2026-05-10 | Revert "Revert "Revert "feat(meta): integrate early workflow workspace UI""" | `1/143` | Low shared AI/meta UI conflict history | Ignore unless AI integration is reopened |
| `codex/ai-gateway-ollama-provider` | `a44144b` | 2026-05-10 | docs(repo): add branch consolidation plan | `1/137` | Low AI provider planning | Ignore for this phase |
| `codex/integration-meta-ocr-labtools-carryover` | `8d83bb6` | 2026-05-18 | feat(bioinformatics): route AI drafts through role-based gateway | `113/133` | Medium shared integration/OCR context | Reference only |
| `codex/integration-labtools-ui-c2-carryover` | `9d4edf3` | 2026-05-29 | Wire release UI gate buttons | `513/82` | Low for Bio/Meta analysis; high for LabTools | Exclude from Bio/Meta migration |

## High-Relevance Branch Findings

| Branch | Files/areas observed | Developed material observed | Current availability | Main risk |
| --- | --- | --- | --- | --- |
| `dev/release-internal-test` | `app/bioinformatics/enrichment/`, `app/bioinformatics/gsea/`, `app/bioinformatics/deg_engine/r_*`, `app/bioinformatics/reports/integrated.py`, `app/bioinformatics/plots/real_svg.py`, `analysis_ui/capability_map.py` | ReleaseBuild-oriented Bio DEG R backends, enrichment production gates, report renderer/runtime policies, real SVG plot split, capability map | Not current UI source of truth; current branch has many equivalent older flat modules but not all ReleaseBuild restructuring | Large divergent tree; direct carry-over would overwrite current contracts |
| `stable/mainline` | Bio formal DEG MVP, analysis UI gates, result/report/plot files | Older MainLine formal DEG MVP | Superseded by current branch for Bio DEG L3 proof | Older than current B52+ and Meta Phase 3 |
| `codex/releasebuild-formal-deg-carryover` | Risk score, report-ready, calibration/DCA plot gates, internal test gate | Risk score / nomogram / ReleaseBuild internal gates | Not current; must not be called production clinical | Clinical-overclaim risk and dependency on ReleaseBuild state |
| `codex/mainline-survival-clinical-carryover` | Enrichment gates, R adapter, enrichment plot/report gates | ORA/GSEA convergence and UI wiring | Current branch has enrichment flat modules and tests; branch may contain convergence docs not current | Needs mapping before reuse |
| `dev/meta-analysis` | Meta OCR worker, PaddleOCR subprocess, LaunchServices package fixes | OCR/fulltext integration history and package handling | Not current; current Meta has fulltext services but not necessarily OCR package chain | External OCR dependency and app-bundle divergence |
| `codex/meta-workflow-ui` | Workflow UI later stages, dedup page, early workspace UI | Early Meta workflow UI | Mostly superseded by current `app/meta_analysis/pages/**` | Current UI should not be replaced |
| `codex/bio-geo-real-download-test` | GEO recognition, DEG runner, PubMed candidate handoff, governance | Old GEO recognition/download and DEG runner hardening | Current branch has newer recognition/standardization/resolver contracts | Legacy path bypass risk |
| `codex/stage-3.6-deg-preflight` | DEG executor preflight, result index to report manifest | Old DEG preflight and report draft links | Current branch has stronger DEG formal gates | Pre-B8 contract semantics |

## Remote Branches

`git branch -r` returned no remote branch entries in this worktree. This audit is therefore based on local branch refs and current legacy directories only.

## Audit Conclusion

There are many historical implementations, but no old branch is safe to merge wholesale. The highest-value migration sources are narrow pieces from `dev/release-internal-test`, `codex/releasebuild-formal-deg-carryover`, `codex/mainline-survival-clinical-carryover`, and `dev/meta-analysis`; all must be reintroduced only through adapters or rewrites against the current UI and contract layers.

