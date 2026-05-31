# UI Route Feature Inventory

Date: 2026-05-29

Purpose: track every visible button, card, route, page, handler, runtime, artifact, and test before any feature is declared connected or migrated.

Allowed statuses:

`connected`, `partial`, `placeholder`, `empty-button`, `missing-handler`, `missing-target-page`, `old-page`, `figma/new`, `broken`, `not migrated`

Allowed page styles:

`figma/new`, `old`, `hybrid`, `placeholder`, `missing`, `unknown`

## Route Inventory

| Module | UI Text | Source UI Baseline | File | objectName/handler | Click Result | Target Page | Runtime | Test | Status | Page Style |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Shell | Welcome / enter local workspace | `9d4edf3` preview | needs audit | needs audit | needs audit | needs audit | none expected | needs audit | partial | unknown |
| Shell | About | `9d4edf3` preview | needs audit | needs audit | needs audit | needs audit | none expected | needs audit | partial | unknown |
| Shell | Settings | `9d4edf3` preview | needs audit | needs audit | needs audit | needs audit | needs audit | needs audit | partial | unknown |
| Project | Project Management | `9d4edf3` preview is regressed | needs source search | needs audit | image-only/regressed | missing complete project page | needs audit | missing | broken | missing |
| Bioinformatics | Module home buttons | `9d4edf3` preview visual only | needs audit | needs audit | needs audit | needs audit | needs audit | needs audit | not migrated | unknown |
| Meta Analysis | Module home buttons | `9d4edf3` preview visual only plus Phase 4 L3 separately | needs audit | needs audit | needs audit | needs audit | needs audit | needs audit | not migrated | unknown |
| LabTools | Module home buttons | `9d4edf3` preview visual only | needs audit | needs audit | needs audit | needs audit | needs audit | needs audit | not migrated | unknown |

## Audit Rules

- Every user-visible entry must have one row.
- Button existence alone is not connected.
- A row can be marked `connected` only when UI, handler, target page/runtime, output/artifact or state, test, and documentation all exist.
- `old-page` and `placeholder` must not be promoted to complete.

## Historical UI Recovery Commit Matrix

Source: `docs/ui/UI线路既往检查.md`. These rows identify recovery sources only; they do not mark any route as migrated or connected.

Default interpretation for all rows below:

| Field | Value |
| --- | --- |
| Source branch | `codex/integration-labtools-ui-c2-carryover` |
| Status | `recovery-source-confirmed` |
| MainLine status | `not migrated / unknown` |
| Migration method | `scoped plan required` |

### Bioinformatics Recovery Sources

| Module | Route / Page | Historical Commit | Status | Notes |
| --- | --- | --- | --- | --- |
| Bioinformatics | Gate shell and state/action contracts | `08e9bd1cad818195e5a8a3911797d2762abcbf28` | recovery-source-confirmed | Route gate shell source; runtime completeness still requires audit. |
| Bioinformatics | Project Home | `900ba600730bec73872cf1ce6224081515ec7bf4` | recovery-source-confirmed | Same commit also covers Data Source. |
| Bioinformatics | Data Source | `900ba600730bec73872cf1ce6224081515ec7bf4` | recovery-source-confirmed | Requires handler and runtime audit. |
| Bioinformatics | Data Check & Preparation | `62739aab8338bd0ea191e3ad44ce41c2f41b1e41` | recovery-source-confirmed | Historical data check page source. |
| Bioinformatics | Group & Design | `62739aab8338bd0ea191e3ad44ce41c2f41b1e41` | recovery-source-confirmed | Same commit as Data Check & Preparation. |
| Bioinformatics | Analysis Tasks | `4061d7242207d8195fe31ff38c57fc10aa8473bb` | recovery-source-confirmed | Formal actions require runtime gate audit. |
| Bioinformatics | Result & Report | `2d5a560ec2980cb2cc6bde0eda858b022cb8e324` | recovery-source-confirmed | Split from report export. |
| Bioinformatics | Report Export | `2d5a560ec2980cb2cc6bde0eda858b022cb8e324` | recovery-source-confirmed | Export gate remains blocked until artifact proof. |
| Bioinformatics | Workbench surface rebuild | `2063ce81d9b1bed5f75962b425885c1027c3aafa` | recovery-source-confirmed | Current visual surface reference for Bioinformatics. |
| Bioinformatics | Release action wiring | `74c19adeecdd6ad3bff924bd001950948e421295` | recovery-source-confirmed | Wiring must be scoped separately from page visuals. |

### Meta Analysis Recovery Sources

| Module | Route / Page | Historical Commit | Status | Notes |
| --- | --- | --- | --- | --- |
| Meta Analysis | Project and Question pages | `bf6aaf86872ee8db28f9cebcaf03968ff33c4aca` | recovery-source-confirmed | Requires route and handler audit. |
| Meta Analysis | Search and Reference pages | `e551f44718c09ccf90a36888933d715445885fdc` | recovery-source-confirmed | Requires runtime boundary audit. |
| Meta Analysis | Screening / Extraction / ROB pages | `557b6451f7a096c4991fb5b18bbe392f7a56cd5b` | recovery-source-confirmed | Do not overwrite later validated Meta workflow without scoped comparison. |
| Meta Analysis | Result / Report / Export gates | `6fe2295738fc248e5b066e4d35360f6e446c5245` | recovery-source-confirmed | Export remains gated until artifact proof. |
| Meta Analysis | Workbench surface rebuild | `87f3f9a880748c1e35e2aa9c6c5b9b00a55ec0a3` | recovery-source-confirmed | Current visual surface reference for Meta. |
| Meta Analysis | Release connection matrix | `8c4e8bdab560ae99a7fdab2a2c4b6131cc0d8d1a` | recovery-source-confirmed | Wiring must be audited before migration. |

### LabTools Recovery Sources

| Module | Route / Page | Historical Commit | Status | Notes |
| --- | --- | --- | --- | --- |
| LabTools | Navigation shell | `3bf79f4fa36a099b2442ebcdc0e9df865a69bc02` | recovery-source-confirmed | Page style unknown until reconciliation. |
| LabTools | General calculator UI | `ca006ee8a35156e2bb5c396a890942924b4ff99a` | recovery-source-confirmed | Do not assume final Figma/new style. |
| LabTools | Reagent preparation UI | `f18b9a0e650fa9bd3cd76cc260ca8e7c145e4bee` | recovery-source-confirmed | Needs storage/write audit. |
| LabTools | Western blot loading UI | `a33cffeb0103c47d03bbbe68643ad431482e2ca5` | recovery-source-confirmed | Needs page style and runtime audit. |
| LabTools | Boundary pages | `00f4ec6cf68634fb01adb889a9b5041ed16df92c` | recovery-source-confirmed | Boundary pages are not runtime completion proof. |
| LabTools | Workbench surface rebuild | `ed396b49e698dcbb28a973cdb7060cd855dcf7b8` | recovery-source-confirmed | Current visual surface reference for LabTools. |
| LabTools | Workspace main window wiring | `a4edda1409f95a2ab43ffd435b84f3b9bd4180e4` | recovery-source-confirmed | Wiring must be scoped separately from `app/labtools/**`. |
