# Project Control Next Phase Plan

Date: 2026-05-29

Project control source: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

Current branch: `dev/bioinformatics`

Current completed facts:

| Completed fact | Commit |
| --- | --- |
| Bioinformatics controlled formal DEG current UI single-point L3 proof | `8036e50d919695c6c6a15cc0ea6b45799bcd4ae9` |
| Meta Analysis Phase 3 result contract unification | `5c435a8aa75650dded37b7f6ad7da83a9c5e422d` |
| Phase 2.5 branch inventory and migration candidate audit | `eee6f3d3520a043894a7a4a7947af7b87d1d03c7` |

## Control Boundary

This document is a project control and integration plan only. It does not authorize code development, UI modification, legacy feature migration, branch merge, or cherry-pick.

All future implementation work must start from the current mainline by opening a new feature branch from `dev/bioinformatics` at or after `eee6f3d3520a043894a7a4a7947af7b87d1d03c7`.

## Unique Mainline

The only current mainline is:

```text
dev/bioinformatics
```

The current mainline owns the active Bioinformatics UI, active Meta Analysis UI, Bio controlled formal DEG L3 single-point proof, Meta Phase 3 canonical result contract bridge, and Phase 2.5 audit decisions.

No legacy branch, old `legacy/` directory, or historical UI branch is a parallel mainline. Current UI paths and current contracts remain the source of truth.

## Material Libraries Only

The following branches may be read as material libraries, but must not be merged wholesale, cherry-picked wholesale, or treated as current runtime truth.

| Branch / source | Allowed use | Control disposition |
| --- | --- | --- |
| `dev/release-internal-test` | Bio DEG R adapters, enrichment/resource gates, integrated report and renderer policy candidates | High-value material library; adapter only |
| `stable/mainline` | Historical Bio formal DEG and MainLine carry-over evidence | Historical baseline only |
| `dev/meta-analysis` | Meta OCR/fulltext/package history and LaunchServices handling | Selective reference only; not current Meta runtime |
| `dev/integration` | Integration registry and UI rebuild history | Contract reference only |
| `codex/releasebuild-formal-deg-carryover` | Risk score, nomogram, calibration/DCA and ReleaseBuild gate evidence | Rewrite source only; no clinical production claim |
| `codex/mainline-survival-clinical-carryover` | Enrichment convergence and survival/clinical evidence | Adapter/rewrite source only |
| `codex/meta-workflow-ui`, `codex/meta-analysis-refresh` | Old Meta UI workflow references | UI reference only; do not replace current UI |
| `codex/bio-geo-real-download-test`, `codex/bio-search-ui-main*`, `codex/bio-ui-download-integration` | Old GEO search/download/profile refinements | Reference only |
| Shared vocabulary, AI gateway, LabTools, UI shell branches | Cross-cutting resource or shell history | Out of Bio/Meta migration scope unless explicitly selected later |
| `app/bioinformatics/legacy/**`, `app/meta_analysis/legacy/**` | Requirements archaeology, fixtures, wording, design reference | Quarantined; not runtime sources |

## Next Phase Priority

| Priority | Phase | Purpose | Entry condition | Exit condition |
| --- | --- | --- | --- | --- |
| P0 | Project control guardrail | Create feature branches only from current `dev/bioinformatics`; keep legacy as read-only material | Any new work request | Branch starts from current mainline; one selected current UI path and one candidate scope are named |
| P1 | Meta Phase 4 UI L3 proof | Prove Meta current UI loop end to end from the same v2 statistics run through canonical contract, table, forest plot, and report/export artifact | Current Phase 3 contract bridge exists | Current Meta UI-driven L3 evidence exists; Meta can be described at the proved level only |
| P2 | Bio DEG production hardening queue | Reuse current Bio formal DEG and adapt missing R/runtime/data-quality gates behind current contracts | P1 completed or explicitly deferred by project control | Controlled current UI proof remains intact; each hardening gate has current tests and output evidence |
| P3 | Bio enrichment queue | Adapt/rewrite ORA/GSEA resource, result, plot, and report gates against current UI and flat/current contracts | DEG hardening scope closed or explicitly separated | ORA/GSEA current UI paths have current tests and real artifact evidence |
| P4 | Bio report/render queue | Adapt integrated report and renderer policies without replacing current result semantics | Supported Bio result contracts are stable | Report/export output is generated from current result contracts only |
| P5 | Bio survival/clinical queue | Preserve controlled KM/Cox gates while keeping clinical conclusions and report-ready claims disabled | Project control approves clinical boundary | Controlled artifacts are tested; no production clinical claim |
| P6 | Late rewrite candidates | Risk score/nomogram, TCGA/GTEx facade rewrite, Meta OCR/fulltext adapter | Earlier L3/proof paths are stable | Each candidate is reintroduced as a new current implementation, not a legacy backflow |

## Meta Phase 4 Decision

Meta Phase 4 comes before old feature migration.

Reason: Phase 3 unified the Meta result contract bridge, but the L3 closure worklog explicitly stops before proving the current Meta UI loop end to end. Starting old feature migration before Meta Phase 4 would mix unproved legacy surfaces into a partially proved current Meta contract. The next Meta work should therefore prove the current UI path first, not import historical Meta workbench, OCR, reporting, or workflow UI code.

Allowed Meta Phase 4 target:

```text
Current Meta UI -> confirmed analysis plan -> v2 statistics run -> canonical contract -> table artifact -> forest plot artifact -> report/export artifact
```

Disallowed during Meta Phase 4:

```text
legacy Meta workbench replacement
legacy reporting placeholder backflow
OCR/fulltext branch migration
old workflow UI replacement
dry-run/no-op runner claims
```

## Bio Migration Queue

Bio controlled formal DEG is already the current proved L3 single-point path and should be preserved, not replaced.

The next Bio queue is:

| Order | Candidate | Source posture | Required control rule |
| --- | --- | --- | --- |
| B1 | Multi-factor DEG focused proof | Current reuse with focused proof | Keep current schema/confirmation/result contracts; add proof before release claims |
| B2 | DEG production hardening gates | Current plus `dev/release-internal-test` material | Adapt only behind current resolver/result index; no direct branch copy |
| B3 | limma/DESeq2/edgeR R runtime adapters | Current plus `dev/release-internal-test` material | Detect external R/Bioc state first; preserve current method controls |
| B4 | ORA enrichment MVP | Current flat modules plus branch package material | Adapter/rewrite only; current UI path and tests required |
| B5 | GSEA preranked MVP | Current flat modules plus branch package material | Adapter/rewrite only; resource/version gates required |
| B6 | Enrichment resource registry | `dev/release-internal-test` material | Introduce as current service contract, not branch package transplant |
| B7 | Real SVG plot renderer generalization | Current renderer plus branch renderer candidates | Preserve source result semantics and artifact provenance |
| B8 | Full integrated report/renderers | Current report/export plus branch runtime policy material | Adapter only; external renderer dependencies must be detect-first |
| B9 | KM/log-rank and Cox controlled proof expansion | Current survival/clinical modules | Keep report-ready and clinical conclusions disabled unless separately proved |
| B10 | Risk score / nomogram / DCA | Branch evidence only | Rewrite later with strict clinical boundary; no production claim |
| B11 | TCGA/GTEx facade gaps | Legacy material only | Rewrite only after current data-source audit; no direct legacy import |

## Legacy Backflow Ban

The following must not flow back into current runtime directly:

| Legacy item | Ban |
| --- | --- |
| Standalone Bio GEO GUI and `run_geo_tool.py` | Do not import or launch from current UI |
| Bio legacy GEO workflow and `geo_pipeline/**` | Do not bypass current B8/B9 resolver and standardized asset contracts |
| Bio literature CLI/GUI | Do not move PubMed/PICO/literature ownership into Bio |
| Legacy GEO download/process scripts | Do not wire compatibility scripts as current task actions |
| Legacy TCGA/GTEx facade | Do not direct-migrate old facade/locator/mock contracts |
| Meta old workbench shell | Do not replace current Meta pages or workflow dashboard |
| Meta fake GEO readiness / DEG-ready matrix | Do not count as real analysis or Meta capability |
| Meta task mock/no-op runner | Do not count as real execution evidence |
| Meta legacy reporting placeholders | Do not count as canonical report/export output |
| Legacy package scripts | Do not use as current app packaging source |
| Legacy icons/contact sheets | Do not treat as functionality; design review only |
| Old pre-B8 DEG preflight | Do not treat as formal DEG evidence |
| Old GEO search UI branches | Do not overwrite current search/recognition services |
| Old Meta workflow UI branch | Do not replace current UI; reference only |

## Integration Rules For All Future Tasks

1. Start from current `dev/bioinformatics`.
2. Create a feature branch before implementation.
3. Name one current UI path and one contract boundary before coding.
4. Use old branches and `legacy/**` only as read-only material libraries.
5. Do not merge or cherry-pick old branches.
6. Do not replace current UI with historical UI.
7. Do not migrate a legacy feature without a current UI entry, current contract mapping, current tests, and real output evidence.
8. Preserve existing disabled boundaries for GSEA/survival/clinical/report-ready claims until separately proved.
9. Keep Meta Phase 4 ahead of old feature migration unless project control explicitly records a deferral.
10. Keep unrelated untracked files and unrelated worktree state untouched.

## Stop Point

Stop after this plan. No functional development, UI modification, legacy migration, merge, or cherry-pick is part of this project control handoff.
