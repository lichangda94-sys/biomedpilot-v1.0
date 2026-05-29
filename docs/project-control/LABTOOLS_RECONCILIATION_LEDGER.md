# LabTools Reconciliation Ledger

Date: 2026-05-29

Purpose: reconcile LabTools pages and runtime sources before any LabTools page is migrated into MainLine or marked as final UI.

Page style values: `figma/new`, `old`, `hybrid`, `placeholder`, `missing`, `unknown`

Migration priority values: `P0`, `P1`, `P2`, `P3`, `blocked`

## Ledger

| Feature | Best source branch/commit | Current UI route | Page style | Runtime exists | Test exists | Migration priority | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| General reagent calculator | needs audit | needs audit | unknown | needs audit | needs audit | P1 | Do not assume current page is final Figma/new UI. |
| Reagent preparation | needs audit | needs audit | unknown | needs audit | needs audit | P1 | Check storage/session behavior. |
| Western Blot | needs audit | needs audit | unknown | needs audit | needs audit | P1 | Includes loading, ROI, report/export variants. |
| SDS-PAGE | needs audit | needs audit | unknown | needs audit | needs audit | P2 | Verify if separate page or WB subroute. |
| BCA | needs audit | needs audit | unknown | needs audit | needs audit | P2 | Verify runtime and result persistence. |
| PCR/qPCR | needs audit | needs audit | unknown | needs audit | needs audit | P2 | Verify calculator and template sources. |
| ELISA | needs audit | needs audit | missing | needs audit | missing | P3 | Search old branches before marking absent. |
| Cell experiment records | needs audit | needs audit | unknown | needs audit | needs audit | P1 | Verify data model and persistence. |
| Cell image analysis | needs audit | needs audit | unknown | needs audit | needs audit | P1 | Verify image runtime boundaries. |
| Scratch assay | needs audit | needs audit | unknown | needs audit | needs audit | P2 | Check ImageJ/Fiji dependency gates. |
| Transwell | needs audit | needs audit | unknown | needs audit | needs audit | P2 | Check ImageJ/Fiji dependency gates. |
| Fluorescence/staining | needs audit | needs audit | unknown | needs audit | needs audit | P2 | Check runtime and export contract. |
| ImageJ/Fiji external engine entry | needs audit | needs audit | unknown | needs audit | needs audit | P1 | Must remain dependency-gated. |

## Rules

- Do not mark any LabTools page `figma/new` without page-by-page evidence.
- Do not migrate `app/labtools/**` as part of UI Shell baseline work.
- Do not use old LabTools pages as final UI without an explicit redesign or acceptance decision.
