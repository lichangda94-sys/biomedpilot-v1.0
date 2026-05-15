# Meta M4B Screening Workspace Report - 2026-05-13

## Stage

- Stage name: Meta M4B - Screening Workspace Refinement
- Worktree: `/Users/changdali/Developer/biomedpilot v1.0/Meta`
- Branch: `dev/meta-analysis`
- HEAD before work: `c4418a3 docs(meta): align M4A handoff docs`
- Commit made: yes, after validation, with message `feat(meta): add screening workspace refinement`

## Files Changed

- `app/meta_analysis/services/title_abstract_screening_v2_service.py`
- `app/meta_analysis/pages/screening_page.py`
- `app/meta_analysis/workspace.py`
- `app/meta_analysis/services/formal_report_service.py`
- `tests/meta_analysis/test_title_abstract_screening_v2_service.py`
- `tests/meta_analysis/test_exclusion_criteria_library_service.py`
- `tests/meta_analysis/test_meta_workspace_ui_navigation.py`
- `docs/meta_dev_reports/Meta_M4B_screening_workspace_report_20260513.md`

## User-Facing Behavior

- The existing Meta screening route now shows a Chinese-first `文献筛选` workspace with `标题摘要筛选`, `当前文献库`, user decision controls, structured `排除原因`, compact `当前 PRISMA 计数`, and `下一步：全文管理` copy.
- Literature records in the main screening workspace show user-facing fields only: title, first author/author summary, year, journal, source database, abstract snippet, deduplication status, current screening status, and exclusion reason when present.
- The main screening UI does not expose raw JSON, manifest paths, local workspace paths, or developer-only IDs. Existing developer diagnostics remain collapsed by default.
- Supported user decisions now include `not_screened`, `include`, `exclude`, `uncertain`, `need_full_text`, and reset to unscreened.
- Structured M4B exclusion reasons are exposed with Chinese labels:
  `研究对象不符合`, `干预/暴露不符合`, `对照不符合`, `结局不符合`, `研究类型不符合`, `重复文献`, `非原始研究`, `全文不可获取`, `语言或获取限制`, `其他`.

## Developer-Facing Behavior

- `TitleAbstractScreeningV2Service` now owns the M4B decision constants, suggestion states, final evidence-state labels, structured reason labels, decision validation, reset behavior, and screening summary generation.
- Screening decisions continue to persist through the existing active Meta screening decision files and compatibility `screening_decisions.json`, with audit and research governance events.
- Suggestions now remain explicitly suggestion-only as `suggested_include`, `suggested_exclude`, `suggested_uncertain`, or `suggested_need_full_text`; they do not write final screening decisions or advance PRISMA counts.
- Screening summary counts are available as `title_abstract_screening_summary_v1.json` and include imported, after-dedup, unscreened, included, excluded, uncertain, full-text-needed, full-text-included, and full-text-excluded counts.
- Existing PRISMA collection remains compatible with the new `need_full_text` decision by reading compatibility/legacy decision semantics.

## Validation

Commands run:

```bash
git diff --check
```

Result: passed with no output.

```bash
python3 -m pytest tests/meta_analysis -q
```

Result: `465 passed in 4.35s`.

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
```

Result: `154 passed in 10.14s`.

```bash
QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test
```

Result: passed.

Observed smoke output:

```text
BioMedPilot / 医研智析
app_version=0.1.0-internal-beta
app_channel=Developer Preview / testing
launch_mode=source
app_root=/Users/changdali/Developer/biomedpilot v1.0/Meta
git_head=c4418a3
workspace_entries=2
bioinformatics_features=5
meta_analysis_features=7
pyside6_available=True
```

## Limitations

- This stage does not implement statistical analysis, full-text extraction, real AI automatic exclusion, network retrieval, package builds, or remote pushes.
- Full-text management is only the next-step destination label in this stage; the dedicated M4C refinement remains future work.
- Existing Meta outputs remain `Developer Preview / testing` and must not be treated as production, clinical, regulatory, submission-ready, or publication-ready results.
- Screening suggestions remain suggestions until a user accepts or edits them.

## Remaining Dirty / Untracked Files

- Expected pre-existing untracked input artifact remains: `docs/meta_dev_reports/Meta_handoff_report_20260513.md`.
- No unrelated dirty files were observed before this stage. Runtime code, tests, and this report are in-scope for the M4B commit.
