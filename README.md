# BioMedPilot / 医研智析 - Meta Worktree

This worktree is the BioMedPilot v1.0 Meta Analysis development workspace:

```text
/Users/changdali/Developer/biomedpilot v1.0/Meta
```

Current branch: `dev/meta-analysis`
Current handoff HEAD: `76f9a0e`
Status: `Developer Preview / testing`

Meta is for literature-based medical Meta Analysis workflows. It is not a Bioinformatics workspace and must not handle GEO / TCGA / GTEx expression-data analysis. It is also not production-ready, clinical-grade, regulatory-ready, submission-ready, or publication-ready statistical software.

## Runtime Boundary

The active Meta runtime is present in this worktree. It includes active desktop workflow pages, services, adapters, project workspace handling, tests, and testing-level report/export paths.

The legacy bridge has been retired. Active Meta runtime code must not call `app/meta_analysis/legacy/**` through `_legacy_path()`, `LEGACY_ROOT`, legacy service loaders, legacy parsers, or legacy normalizers.

`app/meta_analysis/legacy/**` remains in this branch only as a historical isolation area and reference snapshot. Do not delete it, move it, merge it wholesale into MainLine, or build new features on top of it.

## Current User-Facing Workflow

The current Meta workflow is Chinese-first and testing-level:

1. Project setup: create or open a Meta project and review workflow status.
2. Research question: draft and confirm PICO / PICOS / PECO and protocol fields.
3. Literature search/import: draft search strategy, export strategy, import local NBIB / RIS / CSV files, and optionally hand off selected testing-level PubMed candidates.
4. Deduplication: review duplicate groups, make manual duplicate decisions, and generate a deduplicated set for screening.
5. Screening: perform title/abstract screening with manual include / exclude / uncertain / needs-review decisions and recorded exclusion reasons.
6. Full-text handling: manage full-text status, PDF attachments, unavailable full text, testing-level parsing, and full-text eligibility decisions.
7. Data extraction: manually create study units and effect rows, import/export CSV drafts, and review extraction validation messages.
8. Quality assessment: record staged/testing quality assessments that require user confirmation.
9. Analysis plan: draft and confirm analysis setup before any statistical execution.
10. Statistical analysis placeholder/testing status: testing-level dataset building, statistics helpers, figures, and tables exist, but outputs are not formal publishable results.
11. Report generation roadmap: testing-level Markdown/HTML/DOCX report artifacts, PRISMA summaries, supplementary exports, snapshots, and reproducibility packages exist as draft/reporting foundations.

## Current Limitations

- All Meta features are `Developer Preview / testing`.
- PubMed candidate retrieval is a testing preview, not a complete formal systematic-review search.
- WOS / Embase / Cochrane / CNKI / WanFang / VIP online retrieval is draft, network-dependent, export-oriented, or not fully implemented unless current code and tests prove otherwise.
- Screening remains manual or assisted-only. The system must not automatically turn suggestions into final include/exclude decisions.
- AI and rule-based outputs are suggestions only; they are not accepted evidence until a user accepts or edits them.
- Quality tools are staged/testing workflows and require user confirmation before being treated as project decisions.
- Full-text parsing is testing-level, does not include OCR, and must not automatically convert PDF content into confirmed evidence.
- Statistical outputs must not be treated as formal publishable, clinical, regulatory, or submission-ready results unless produced by a future validated executor.
- Report artifacts are draft/testing outputs. They must clearly distinguish user-confirmed content, system suggestions, testing-level output, real statistical results, and unfinished sections.

## Next Development Stages

- M4B - Screening workspace refinement: make the literature screening workspace clear, Chinese-first, and directly operable for title/abstract screening, exclusion reasons, conflict state, PRISMA count preview, and transition to full text.
- M4C - Full-text management workspace: manage whether full text is needed, uploaded, unavailable, pending inspection, confirmed, or excluded. Do not implement automatic PDF scientific conclusion extraction.
- M5 - Extraction table and evidence-state governance: build structured extraction tables for study metadata, PICO/PECO, effect measures, statistical fields, and draft/suggested/user_accepted/user_edited/confirmed/rejected states.
- M6 - Quality assessment user workflow: implement a clickable, savable, reportable user workflow for one priority tool first, preferably NOS for observational studies or ROB2 for RCTs.
- M7 - Statistical plan confirmation: confirm study type, effect measure, fixed/random model, heterogeneity, subgroup, sensitivity, publication-bias plan, and sufficiency before real execution.
- M8 - Report draft generation: generate structured Markdown report drafts before Word/PDF polish.
- M9 - Real statistical executor integration audit: audit real statistical executor inputs, assumptions, validation baselines, output labels, and safety boundaries before integration.

## Run

```bash
python3 -m app.main
```

For automated startup checks without entering the GUI event loop:

```bash
QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test
```

If `PySide6` is unavailable, the launcher prints a console smoke summary instead of opening the desktop window.

## Test

Meta worktree validation defaults:

```bash
git diff --check
python3 -m pytest tests/meta_analysis -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test
```

For documentation-only changes, full business tests may be skipped only when no runtime code, runtime config, package script, or test file changed. The handoff must state which checks were run and why any larger test set was skipped.

## Packaging

Do not package internal beta or release builds from this Meta module worktree. Packaging must be performed from `ReleaseBuild` after validated MainLine or validated release-source sync.
