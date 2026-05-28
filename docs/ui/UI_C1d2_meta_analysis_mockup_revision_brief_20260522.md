# UI-C1d2 Meta Analysis Mockup Revision Brief

## 1. Purpose

This brief converts the mockup QA findings into practical revision instructions for the Meta Analysis high-fidelity mockup set. It is an implementation input document, not a runtime implementation task.

## 2. Global Rules

Must apply to all mockups:

- Keep `Developer Preview / 本地测试版` visible.
- Keep `English-first processing` visible.
- Keep `AI suggestion only` advisory and subordinate to reviewer decisions.
- Keep `Report not ready` / draft / disabled export states visible.
- Do not show Network Meta as active.
- Do not show CNKI / WanFang / VIP direct retrieval as active.
- Do not show Chinese PDF extraction as active.
- Do not show AI automatic conclusion.
- Do not show fake forest plots, fake pooled effects, heterogeneity, publication bias, report-ready success, or active exports.
- Save / Export / Generate / Mark as final actions require disabled, draft-only, or adapter-needed states until a later gate stage.

## 3. Page-by-Page Revision Brief

### META-MOCK-001: Meta Project Home + Workflow Overview

Decision: `accepted`

Must modify:

- None.

Recommended:

- In implementation, make the bottom Gate Notice compact or collapsible if it consumes too much vertical space.

Keep:

- Unified sidebar.
- Workflow overview.
- Developer Preview, English-first, AI suggestion only, Report not ready chips.
- Mock topic and project summary.

Redraw needed: no.

### META-MOCK-002: Question & Meta Type Selection

Decision: `accepted`

Must modify:

- None for this visual candidate.

Recommended:

- During implementation mapping, align visible Meta type cards with the active v1 registry.
- Treat `Other type` as a non-executable placeholder if retained visually.

Keep:

- No Notes & Confirmation.
- No reviewer confirmation checkbox.
- No bottom boundary notice.
- Network Meta planned / not available.

Redraw needed: no.

### META-MOCK-003: Search Strategy Builder

Decision: `accepted_with_minor_revision`

Must modify:

- Change `Save Draft` to `Save Draft - adapter needed` if storage is not connected.
- Make database selections read as `draft selection`, not executed search.

Recommended:

- Add a short helper line near database selection: `Selected databases define draft scope only; no search has been executed.`

Keep:

- English query editor.
- Term groups.
- Boolean logic controls.
- Fields/filters.
- No Chinese direct retrieval.

Redraw needed: no.

### META-MOCK-004: Import / Reference Management + Deduplication

Decision: `accepted_with_boundary_review`

Must modify:

- Ensure `Import` action is disabled or labelled `preview / adapter needed` in implementation.
- Ensure `Compare` and dedup actions do not imply automatic merge.
- Ensure `Next: Deduplication` is route-only and does not perform deduplication.

Recommended:

- Add a small state label: `Local Draft Only / Not Executed`.
- Keep duplicate risk counts as draft counts.

Keep:

- Import Sources.
- Reference List.
- Deduplication Panel.
- No automatic merge/delete/screening handoff.

Redraw needed: no.

### META-MOCK-005: Screening Workspace

Decision: `accepted_with_minor_revision`

Must modify:

- Rename `Submit Decision` to `Save Draft Decision`.
- Label screening progress as `draft counts`, not final PRISMA counts.

Recommended:

- Add helper text under AI suggestion: `Advisory only; reviewer decision is authoritative.`

Keep:

- Reference queue.
- Reference detail.
- Include draft / Exclude draft / Uncertain / Need full text.
- Decision log.

Redraw needed: no.

### META-MOCK-006: Extraction + Risk of Bias

Decision: `accepted_with_minor_revision`

Must modify:

- Keep `Mark as Draft Extracted`; do not shorten to `Mark as Extracted`.
- Keep Save Draft storage as disabled / adapter-needed if the store is not connected.
- Keep risk-of-bias scores as preview only and requiring final reviewer confirmation.

Recommended:

- Add a small warning near effect values: `Mockup-only draft extraction values; not analysis input.`

Keep:

- Full-text library.
- Type-specific extraction form.
- Draft effect values and CI fields.
- Risk-of-bias draft/in-progress state.

Redraw needed: no.

### META-MOCK-007: Result Review + Report-ready Gate

Decision: `accepted_with_boundary_review`

Must modify:

- Ensure pairwise table is labelled `draft input preview`, not `analysis result`.
- Ensure any `Done` chips mean upstream draft completion, not evidence completion.

Recommended:

- Keep the page as the main location for concentrated gate and human-review copy.

Keep:

- `testing_summary_only`.
- No formal pooled effect.
- Forest plot disabled.
- Report-ready blocked.
- Export gate disabled.

Redraw needed: no.

### META-MOCK-008: Report Export Gate

Decision: `accepted_with_boundary_review`

Must modify:

- Change `Enable Export after Gate` to `Export will be enabled after gate`, or keep the button disabled.
- Keep all format buttons disabled.

Recommended:

- Label report template entries as `draft template preview`.
- Keep export history empty unless a future stage supplies real records.

Keep:

- Report-ready gate not passed.
- DOCX / HTML / PDF / CSV / XLSX / ZIP disabled.
- Draft report/export status.

Redraw needed: no.

## 4. Implementation Guidance

UI-C2a should convert these mockups into state/action contracts before runtime work:

- page key and route mapping
- status chip mapping
- allowed vs disabled action matrix
- AI suggestion boundary
- English-first processing boundary
- Network Meta planned state
- result/report/export gates
- no-file-write checks for export pages

UI-C2a must not enable executor, statistics, report generation, or export.

## 5. Pages That Can Feed UI-C2a Planning

First implementation planning batch:

- Meta Project Home
- Question & Meta Type
- Search Strategy Builder
- Import / Reference Management + Deduplication
- Screening Workspace

Second planning batch:

- Extraction + Risk of Bias
- Result Review + Report-ready Gate
- Report Export Gate

Still blocked:

- Network Meta
- Chinese database direct retrieval
- Chinese PDF extraction
- formal pooled results
- forest plot rendering
- report-ready package
- formal export
