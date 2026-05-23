# Meta Analysis UI-C2c Search Strategy + Reference Management Gated Pages

## Scope

This stage implemented the second Meta Analysis gated runtime batch inside the existing target IA shell:

- Search Strategy / 检索策略
- Import / Reference Management / Deduplication

The implementation is draft and preview UI only. It does not run searches, import files, merge/delete references, send references to screening, generate results, generate reports, or enable export.

## Runtime Changes

### Search Strategy

Added `metaSearchStrategyRuntimePanel` for `search_strategy` with:

- English query draft status
- local draft only status
- search execution disabled status
- term group table:
  - disease terms
  - biomarker terms
  - outcome terms
- Boolean logic preview
- PubMed-style query draft
- database draft scope buttons:
  - PubMed
  - Embase
  - Web of Science
- `Copy Query` safe action
- disabled `Save Draft - adapter needed`

Gate properties:

- `runtimeStatus=testing`
- `processingMode=english_first`
- `aiBoundary=advisory_only`
- `resultSemanticKey=no_formal_result`
- `reportStatusKey=report.status.draft`
- `exportGate=disabled_empty_result`
- `formalActionEnabled=false`

### Reference Management + Deduplication

Added `metaReferenceDedupRuntimePanel` for `import_dedup` with:

- disabled import source cards:
  - RIS / BibTeX / EndNote XML
  - CSV / Excel
  - PubMed result file
  - Manual entry
- mockup-only / local draft reference table preview
- duplicate risk group preview
- reviewer review required status chip
- disabled mutating actions:
  - Auto merge disabled
  - Auto delete disabled
  - Send to screening disabled

Gate properties remain the same draft-only / no-formal-result boundaries as Search Strategy.

## Explicit Non-Changes

This stage did not:

- execute PubMed / Embase / Web of Science search
- enable CNKI / WanFang / VIP / Chinese database direct retrieval
- enable Chinese PDF extraction
- import RIS / BibTeX / CSV / EndNote files
- automatically merge duplicate references
- automatically delete references
- automatically send references to screening
- create final included studies
- enable any Meta executor
- generate pooled effects, forest plots, heterogeneity, or publication-bias results
- generate report-ready package
- enable DOCX / HTML / PDF / CSV / XLSX export
- enable Network Meta
- package or run the packaged app
- touch UI-B10 / App icon / Finder icon / `.icns` / `Info.plist` / LaunchServices

## Test Coverage

Added `tests/ui/test_meta_analysis_search_reference_gated_pages.py` covering:

- Search Strategy renders English query draft only.
- Database selections are draft scope and have `executedSearch=false`.
- Copy Query is safe and enabled.
- Save Draft remains disabled / adapter-needed.
- Forbidden Chinese direct retrieval surfaces are absent.
- Reference import source cards exist but real import actions are disabled.
- Reference table preview is mockup-only / local draft.
- Deduplication risk group exists.
- Auto merge / auto delete / send-to-screening remain disabled.
- Result/report/export and Network Meta gates remain disabled.

## Validation

| Command | Result |
|---|---|
| `python3 -m pytest -q tests/ui/test_meta_analysis_search_reference_gated_pages.py` | Passed: 4 tests |
| `python3 -m pytest -q tests/ui/test_meta_analysis_project_question_gated_pages.py` | Passed: 4 tests |
| `python3 -m pytest -q tests/ui/test_meta_analysis_ia_shell.py` | Passed: 10 tests |

Final stage validation must also include the shared Result / Report / Export shell, source smoke, `git diff --check`, and `git diff --cached --check`.

## Current Boundary

Meta Analysis remains Developer Preview / testing. Search and reference management are draft/preview-only gated pages. They do not mutate project data or create evidence artifacts.
