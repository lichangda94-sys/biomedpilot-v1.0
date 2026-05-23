# Meta Analysis UI-C1d2 Mockup Candidate QA Report

## 1. Scope

This QA stage reviews eight high-fidelity Meta Analysis mockup candidates against:

- `docs/ui/UI_C1d_meta_analysis_workflow_mockup_plan_20260522.md`
- `docs/ui/UI_C1d_meta_analysis_screen_specs_20260522.csv`
- `docs/ui/UI_C1d_meta_analysis_mockup_prompt_pack_20260522.md`
- `docs/ui/mockup_data/meta_analysis/UI_C1d_meta_analysis_mockup_sample_data_20260522.md`
- current BioMedPilot unified UI direction

This stage only creates documentation and implementation planning inputs. It does not modify `app/**`, `tests/**`, `assets/**`, `scripts/**`, `dist/**`, or packaging resources.

## 2. Image Path Check

All eight source mockup images were found and validated as PNG image data:

| mockup_id | image_path | detected_size |
|---|---|---|
| META-MOCK-001 | `/Users/changdali/Desktop/UI/界面示意图/Meta/Meta_Project_Home_Workflow_Overview_candidate_v2_20260522.png` | 1586 x 992 |
| META-MOCK-002 | `/Users/changdali/Desktop/UI/界面示意图/Meta/Meta_Question_Meta_Type_Selection_candidate_v2_20260522.png` | 1586 x 992 |
| META-MOCK-003 | `/Users/changdali/Desktop/UI/界面示意图/Meta/Meta_Search_Strategy_Builder_candidate_20260522.png` | 1536 x 1024 |
| META-MOCK-004 | `/Users/changdali/Desktop/UI/界面示意图/Meta/图 4：Import : Reference Management + Deduplication` | 1536 x 1024 |
| META-MOCK-005 | `/Users/changdali/Desktop/UI/界面示意图/Meta/Meta_Screening_Workspace_candidate_20260522.png` | 1536 x 1024 |
| META-MOCK-006 | `/Users/changdali/Desktop/UI/界面示意图/Meta/图 6：Extraction + Risk of Bias` | 1536 x 1024 |
| META-MOCK-007 | `/Users/changdali/Desktop/UI/界面示意图/Meta/Meta 图 7：Result Review + Report-ready Gate` | 1536 x 1024 |
| META-MOCK-008 | `/Users/changdali/Desktop/UI/界面示意图/Meta/Meta_Report_Export_Gate_candidate_20260522.png` | 1536 x 1024 |

## 3. Overall QA Conclusion

The mockup set is suitable for the next planning stage: **Meta UI-C2a Implementation Gate / State Planning**.

It should not move directly into runtime implementation or executor integration. The images need a small amount of text and boundary tightening, primarily around draft decision wording, disabled export language, and avoiding front-loaded human-review blocks on early workflow pages.

## 4. Per-Mockup Review

### A. Meta Project Home + Workflow Overview

Decision: `accepted`

Passes:

- Uses unified BioMedPilot sidebar with Dashboard / Bioinformatics / Meta Analysis / LabTools / Settings.
- Shows workflow overview and project summary.
- Makes Developer Preview, English-first processing, AI suggestion only, and Report not ready visible.
- Does not show fake result, forest plot, pooled effect, report-ready success, active export, CNKI, WanFang, or VIP direct retrieval.
- Current mock topic is clearly marked as mock/demo and non-production.

Notes:

- The bottom Gate Notice is acceptable on the project home as a system-level boundary strip. For implementation, it can be compact or collapsible so the first page does not become dominated by review-warning text.

### B. Question & Meta Type Selection

Decision: `accepted`

Passes:

- Focuses on research question, English question, PICO/PECO draft, Meta type selection, Network Meta planned state, and next-step navigation.
- Removes Notes & Confirmation, reviewer confirmation checkbox, and bottom boundary block.
- Network Meta is explicit as planned / not available.
- Does not show search results, pooled effect, forest plot, report-ready success, or active export.

Notes:

- The visible type card set is visually acceptable for this mockup. During implementation planning, map it back to the current active type registry and avoid treating `Other type` as an executable analysis path.

### C. Search Strategy Builder

Decision: `accepted_with_minor_revision`

Passes:

- Focuses on English query construction, term groups, Boolean logic, fields/filters, and database draft selection.
- Does not show Chinese database direct retrieval.
- Does not show executed search results.
- PubMed / Embase / Web of Science are presented as draft database selections, not confirmed executions.

Required text revision:

- `Save Draft` should be labelled `Save Draft - adapter needed` or shown as a draft-only action if storage is not connected.

Implementation note:

- Keep database checkboxes as selection/draft scope only. They must not trigger real retrieval.

### D. Import / Reference Management + Deduplication

Decision: `accepted_with_boundary_review`

Passes:

- Clear second/third-level structure: Import Sources, Reference List, Deduplication Panel.
- Shows reference table and duplicate groups.
- Explicitly states no automatic merge, no automatic delete, and no auto-send to screening.
- Does not show formal included studies or finalized screening results.

Boundary review needed:

- Buttons such as `Import`, `Compare`, and `Next: Deduplication` must remain preview/gated until import and dedup adapters are explicitly planned.
- Deduplication counts should remain local draft counts and should not update PRISMA or final included-study counts.

### E. Screening Workspace

Decision: `accepted_with_minor_revision`

Passes:

- Shows reference queue, detail pane, screening decision panel, decision log, and screening progress.
- Uses draft states: Include draft, Exclude draft, Uncertain, Need full text.
- AI suggestion is a small advisory notice and does not appear as a final decision.

Required text revision:

- `Submit Decision` should become `Save Draft Decision` or be labelled `draft / not final`.
- Screening counts should be labelled `draft counts`, not final PRISMA counts.

Implementation note:

- Keep reviewer action authoritative. AI suggestion must never write final screening status by itself.

### F. Extraction + Risk of Bias

Decision: `accepted_with_minor_revision`

Passes:

- Shows full-text library, data extraction form, and risk-of-bias assessment.
- Extraction values and confidence intervals are visibly mockup/draft data.
- Risk-of-bias scores are marked draft / in progress / preview.
- No Chinese PDF automatic extraction, automatic final extraction, automatic bias judgement, formal pooled effect, forest plot, report-ready success, or active export is shown.

Required text revision:

- `Mark as Draft Extracted` is correctly safer than `Mark as Extracted`; keep this wording.
- `Save Draft` should remain adapter-needed if storage is not connected.
- Risk-of-bias score must keep `requires final reviewer confirmation`.

Implementation note:

- Do not treat mock effect values as real analysis input.

### G. Result Review + Report-ready Gate

Decision: `accepted_with_boundary_review`

Passes:

- Concentrates human review and result boundary messaging on the proper late-stage page.
- Shows `testing_summary_only`.
- Shows no formal meta-analysis has been performed.
- Forest plot, pooled effect, heterogeneity, and publication bias are unavailable.
- Report status is draft; report-ready is blocked.
- Export gate is disabled.

Boundary review needed:

- The pairwise input preview table can remain as draft input preview, but must not be interpreted as an analysis output table.
- Any `Done` chips in readiness summary must mean upstream draft completion only, not final evidence completion.

Implementation note:

- This page is the correct place for concentrated manual-review and gate messaging.

### H. Report Export Gate

Decision: `accepted_with_boundary_review`

Passes:

- Focuses on Report Export / 报告导出.
- Shows Report-ready Gate not passed.
- DOCX / HTML / PDF / CSV / XLSX / ZIP export controls are disabled.
- Does not show active export or fake report-ready success.

Required boundary revision:

- `Enable Export after Gate` should either remain disabled or be reworded as `Export will be enabled after gate`.
- Report template rows must remain draft/template previews, not generated report artifacts.

Implementation note:

- This mockup is valid as an export-gate shell reference, not an export implementation.

## 5. Global Revision Rules

Apply these rules before UI-C2 planning:

- Front-loaded pages should not show large human-review blocks.
- Front-loaded pages should not show reviewer confirmation checkboxes.
- Concentrate human review and report/export gate copy in Result Review, Report-ready Gate, and Export pages.
- AI suggestion is always advisory only.
- English-first processing remains visible.
- Chinese input only assists English query drafting; it does not execute Chinese database retrieval.
- Network Meta remains planned / disabled.
- Save, Export, Report-ready, Generate, and final decision actions must remain disabled or gated unless a later stage explicitly adds the adapter and tests.

## 6. Implementation Readiness Summary

Ready for UI-C2a planning:

- Project Home
- Question & Meta Type
- Search Strategy Builder
- Import / Reference Management + Deduplication
- Screening Workspace
- Extraction + Risk of Bias
- Result Review + Report-ready Gate
- Report Export Gate

Not ready for direct runtime implementation:

- Meta executor integration
- Network Meta
- Chinese database direct retrieval
- Chinese PDF extraction
- formal forest plot or pooled effect rendering
- report-ready package
- export

## 7. Next Stage Recommendation

Recommended next stage:

- `Meta UI-C2a Implementation Gate / State Planning`

Do not directly enter runtime implementation. UI-C2a should first define page state, action gates, result/report/export gates, disabled actions, test strategy, and adapter boundaries.

## 8. Validation

Required validation:

```bash
python3 - <<'PY'
from pathlib import Path
from PIL import Image
paths = [...]
for path in paths:
    assert Path(path).exists()
    Image.open(path).verify()
print("8 image paths ok")
PY
python3 - <<'PY'
import csv
from pathlib import Path
path = Path('docs/ui/UI_C1d2_meta_analysis_mockup_to_implementation_mapping_20260522.csv')
with path.open(newline='') as fh:
    rows = list(csv.DictReader(fh))
assert len(rows) == 8
print("mapping csv ok")
PY
git diff --check
git diff --cached --check
```

Results:

| Command | Result |
|---|---|
| 8 image path check with PIL verify | passed |
| CSV structure check for `UI_C1d2_meta_analysis_mockup_to_implementation_mapping_20260522.csv` | passed, 8 rows |
| `git diff --check` | passed |

`git diff --cached --check` is run after staging the scoped UI-C1d2 files.
