# Meta Analysis UI-C2a Implementation Gate / State Planning

## 1. Scope

This stage prepares Meta Analysis runtime UI implementation by defining page state, action gates, result/report/export gates, implementation sequence, and test strategy.

This stage does not:

- implement runtime pages
- modify `app/**`
- modify `tests/**`
- add Meta backend features
- enable Meta executors
- enable Network Meta
- enable Chinese database direct retrieval
- enable Chinese PDF extraction
- generate fake forest plots, pooled effects, heterogeneity, or publication-bias results
- generate report-ready packages
- enable DOCX / HTML / PDF / CSV / XLSX export
- run packaging or packaged app
- touch UI-B10 / App icon / Finder icon / `.icns` / `Info.plist` / LaunchServices

## 2. Inputs

Reviewed planning and QA inputs:

- `docs/ui/UI_C1d_meta_analysis_workflow_mockup_plan_20260522.md`
- `docs/ui/UI_C1d_meta_analysis_screen_specs_20260522.csv`
- `docs/ui/UI_C1d_meta_analysis_mockup_prompt_pack_20260522.md`
- `docs/ui/mockup_data/meta_analysis/UI_C1d_meta_analysis_mockup_sample_data_20260522.md`
- `docs/ui/UI_C1d2_meta_analysis_mockup_candidate_QA_report_20260522.md`
- `docs/ui/UI_C1d2_meta_analysis_mockup_revision_brief_20260522.md`
- `docs/ui/UI_C1d2_meta_analysis_mockup_to_implementation_mapping_20260522.csv`
- `app/meta_analysis/workspace.py`
- `app/shared/result_report_export_shell.py`
- `tests/ui/test_meta_analysis_ia_shell.py`

## 3. Current Runtime Baseline

Current Meta Analysis runtime is a target IA shell with:

- 10 main-flow pages
- auxiliary Meta Settings
- 10 active Meta type cards
- Network Meta planned / disabled
- Full-text & Extraction tab concept
- shared Result / Report / Export gated shell

It is not a full production Meta workflow. The mockups should be implemented as gated shell pages first.

## 4. State Model Summary

Detailed state/action contract:

- `docs/ui/UI_C2a_meta_analysis_state_action_gate_contract_20260522.md`

Required global page states:

- Developer Preview / testing
- English-first processing
- AI suggestion only
- local draft only
- no formal result
- report not ready
- export disabled

Required workflow states:

- `project_home`
- `question_type`
- `search_strategy`
- `reference_management`
- `deduplication`
- `screening`
- `fulltext_extraction`
- `risk_of_bias`
- `pairwise_input`
- `result_review`
- `report_ready_gate`
- `export`

## 5. Action Gate Model Summary

Action categories:

| gate category | allowed examples | rule |
|---|---|---|
| allowed navigation actions | next step, back, select page | No data mutation or executor call. |
| draft-only actions | edit draft question, draft query, draft decision | Must not create final artifacts. |
| reviewer-controlled actions | save draft decision, mark draft extracted | Reviewer remains authority; AI never finalizes. |
| disabled actions | Generate Report, Export, Run Formal Meta | Visible but disabled with reason. |
| blocked_until_backend actions | real import, save extraction, formal RoB | Requires separate backend/adapter stage. |
| future/planned actions | Network Meta, production export | Disabled/planned state only. |

## 6. Page-Level Action Plan

| page | allowed actions | disabled / blocked actions |
|---|---|---|
| Project Home | view workflow, open next step | report/export/formal result disabled |
| Question & Type | edit draft question, choose Meta type draft | Network Meta disabled; no final protocol/search/result |
| Search Strategy | build English query draft, choose database draft scope | no Chinese DB execution; no executed search |
| Import / Reference + Dedup | reference table preview, dedup review preview | no auto merge/delete/send to screening |
| Screening | draft include/exclude/uncertain/full-text decisions | no AI final decision or final included studies |
| Extraction + Risk of Bias | draft extraction / draft RoB preview | no Chinese PDF extraction or auto RoB judgement |
| Pairwise Input | effect-row/preflight preview | no pooled effect, Network Meta, or formal result |
| Result Review + Report-ready Gate | gate preview and blocker review | no formal pooled effect or report-ready success |
| Report Export | export gate preview | all export formats disabled |

## 7. Result / Report / Export Gate Summary

Detailed RRE gate contract:

- `docs/ui/UI_C2a_meta_analysis_result_report_export_gate_contract_20260522.md`

Required semantics:

- `result_semantic = testing_summary_only / no_formal_result`
- `report_status = draft / blocked / not_ready`
- `export_gate = disabled_empty_result / report_not_ready / adapter_missing`
- `forest_plot = disabled_boundary`
- `pooled_effect = none`
- `heterogeneity = none`
- `publication_bias = none`
- `Network Meta = planned_disabled`
- `reportReadyPackageAllowed = false`
- `fileWriteAllowed = false`

## 8. Implementation Sequence

Detailed implementation sequence:

- `docs/ui/UI_C2a_meta_analysis_page_implementation_sequence_20260522.csv`

Recommended stages:

1. Meta UI-C2b Project Home + Question/Type gated pages.
2. Meta UI-C2c Search Strategy + Reference Management gated pages.
3. Meta UI-C2d Screening + Extraction/Risk of Bias gated pages.
4. Meta UI-C2e Result Review + Report-ready / Export Gate pages.
5. Meta UI-C2f closure audit.

Do not skip directly to executor or result implementation.

## 9. Test Plan

Future implementation stages should add focused UI tests for:

- 10 main-flow pages + Meta Settings IA remains stable.
- page keys and status chips are stable.
- Network Meta remains planned / disabled.
- active Meta types remain from v1 registry direction.
- Search Strategy has no Chinese database direct retrieval action.
- database selection is draft scope, not executed search.
- Import/Reference has no automatic merge/delete/send-to-screening.
- Screening uses draft decisions and AI advisory-only copy.
- Extraction/RoB has no Chinese PDF extraction, no automatic final extraction, and no automatic RoB judgement.
- Pairwise input has no active pooled effect execution.
- Result Review has no fake forest plot, pooled effect, heterogeneity, or publication-bias result.
- Report-ready remains blocked.
- Report Export keeps all DOCX / HTML / PDF / CSV / XLSX / ZIP controls disabled.
- shared Result/Report/Export shell remains gated.
- source smoke passes with `python3 -m app.main --smoke-test`.

## 10. Implementation Readiness

Ready for gated shell implementation planning:

- Project Home
- Question & Meta Type
- Search Strategy
- Import / Reference + Deduplication
- Screening
- Full-text / Extraction + Risk of Bias
- Result Review + Report-ready Gate
- Report Export Gate

Not ready for runtime enablement:

- formal Meta executor
- Network Meta
- Chinese database direct retrieval
- Chinese PDF extraction
- formal pooled effects
- forest plot rendering
- report-ready package
- export

## 11. Required Revision Carry-Forward

From UI-C1d2, implementation planning must carry:

- Rename `Submit Decision` to `Save Draft Decision`.
- Mark screening counts as draft counts.
- Keep `Mark as Draft Extracted`.
- Make `Save Draft` adapter-needed where storage is not connected.
- Reword `Enable Export after Gate` to `Export will be enabled after gate`, or keep it disabled.
- Keep early pages free of large reviewer-confirmation blocks.
- Concentrate manual review and report/export gate copy on Result Review, Report-ready Gate, and Export pages.

## 12. Validation

Required validation for this planning stage:

```bash
python3 - <<'PY'
import csv
from pathlib import Path
path = Path('docs/ui/UI_C2a_meta_analysis_page_implementation_sequence_20260522.csv')
with path.open(newline='') as fh:
    rows = list(csv.DictReader(fh))
assert len(rows) == 5
print(f'{path}: {len(rows)} rows')
PY
git diff --check
git diff --cached --check
```

Results:

| Command | Result |
|---|---|
| CSV structure check for `UI_C2a_meta_analysis_page_implementation_sequence_20260522.csv` | passed, 5 rows |
| `git diff --check` | passed |

`git diff --cached --check` is run after staging the scoped UI-C2a files.

## 13. Conclusion

Meta Analysis UI-C2a is ready to hand off to a gated runtime implementation sequence. The next stage should be:

- `Meta UI-C2b Project Home + Question/Type gated pages`

It must remain shell-first and gate-first. Executor, result, report, and export enablement remain out of scope.
