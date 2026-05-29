# UI Route Feature Inventory

Date: 2026-05-29

Purpose: absorb `docs/ui/UI线路既往检查.md` into Project Control as the initial route recovery matrix. This is an audit-only inventory and not a migration plan.

Default values for absorbed historical rows:

| Field | Value |
| --- | --- |
| `source` | `codex/integration-labtools-ui-c2-carryover` |
| `status` | `recovery-source-confirmed` |
| `mainline_status` | `not migrated / unknown` |
| `migration_method` | `scoped plan required` |

## Inventory Matrix

| Module | Route / Page | Historical Commit | Source | Status | MainLine Status | Migration Method | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Bioinformatics | Gate shell and state/action contracts | `08e9bd1cad818195e5a8a3911797d2762abcbf28` | `codex/integration-labtools-ui-c2-carryover` | recovery-source-confirmed | not migrated / unknown | scoped plan required | Provides route gate shell; not proof of runtime completeness. |
| Bioinformatics | Project Home | `900ba600730bec73872cf1ce6224081515ec7bf4` | `codex/integration-labtools-ui-c2-carryover` | recovery-source-confirmed | not migrated / unknown | scoped plan required | Same commit also covers Data Source. |
| Bioinformatics | Data Source | `900ba600730bec73872cf1ce6224081515ec7bf4` | `codex/integration-labtools-ui-c2-carryover` | recovery-source-confirmed | not migrated / unknown | scoped plan required | Requires handler and runtime audit. |
| Bioinformatics | Data Check & Preparation | `62739aab8338bd0ea191e3ad44ce41c2f41b1e41` | `codex/integration-labtools-ui-c2-carryover` | recovery-source-confirmed | not migrated / unknown | scoped plan required | Historical check identified this as the data check page source. |
| Bioinformatics | Group & Design | `62739aab8338bd0ea191e3ad44ce41c2f41b1e41` | `codex/integration-labtools-ui-c2-carryover` | recovery-source-confirmed | not migrated / unknown | scoped plan required | Same commit as Data Check & Preparation. |
| Bioinformatics | Analysis Tasks | `4061d7242207d8195fe31ff38c57fc10aa8473bb` | `codex/integration-labtools-ui-c2-carryover` | recovery-source-confirmed | not migrated / unknown | scoped plan required | Formal actions still require runtime gate audit. |
| Bioinformatics | Result & Report | `2d5a560ec2980cb2cc6bde0eda858b022cb8e324` | `codex/integration-labtools-ui-c2-carryover` | recovery-source-confirmed | not migrated / unknown | scoped plan required | Split from report export. |
| Bioinformatics | Report Export | `2d5a560ec2980cb2cc6bde0eda858b022cb8e324` | `codex/integration-labtools-ui-c2-carryover` | recovery-source-confirmed | not migrated / unknown | scoped plan required | Export gate must remain gated until runtime/package audit passes. |
| Bioinformatics | Workbench surface rebuild | `2063ce81d9b1bed5f75962b425885c1027c3aafa` | `codex/integration-labtools-ui-c2-carryover` | recovery-source-confirmed | not migrated / unknown | scoped plan required | Current visual surface reference for Bioinformatics. |
| Bioinformatics | Release action wiring | `74c19adeecdd6ad3bff924bd001950948e421295` | `codex/integration-labtools-ui-c2-carryover` | recovery-source-confirmed | not migrated / unknown | scoped plan required | Wiring must be scoped separately from page visuals. |
| Meta Analysis | Project and Question pages | `bf6aaf86872ee8db28f9cebcaf03968ff33c4aca` | `codex/integration-labtools-ui-c2-carryover` | recovery-source-confirmed | not migrated / unknown | scoped plan required | Requires route and handler audit. |
| Meta Analysis | Search and Reference pages | `e551f44718c09ccf90a36888933d715445885fdc` | `codex/integration-labtools-ui-c2-carryover` | recovery-source-confirmed | not migrated / unknown | scoped plan required | Requires runtime boundary audit. |
| Meta Analysis | Screening / Extraction / ROB pages | `557b6451f7a096c4991fb5b18bbe392f7a56cd5b` | `codex/integration-labtools-ui-c2-carryover` | recovery-source-confirmed | not migrated / unknown | scoped plan required | Do not overwrite later validated Meta workflow without scoped comparison. |
| Meta Analysis | Result / Report / Export gates | `6fe2295738fc248e5b066e4d35360f6e446c5245` | `codex/integration-labtools-ui-c2-carryover` | recovery-source-confirmed | not migrated / unknown | scoped plan required | Export remains gated until artifact proof. |
| Meta Analysis | Workbench surface rebuild | `87f3f9a880748c1e35e2aa9c6c5b9b00a55ec0a3` | `codex/integration-labtools-ui-c2-carryover` | recovery-source-confirmed | not migrated / unknown | scoped plan required | Current visual surface reference for Meta. |
| Meta Analysis | Release connection matrix | `8c4e8bdab560ae99a7fdab2a2c4b6131cc0d8d1a` | `codex/integration-labtools-ui-c2-carryover` | recovery-source-confirmed | not migrated / unknown | scoped plan required | Wiring must be audited before migration. |
| LabTools | Navigation shell | `3bf79f4fa36a099b2442ebcdc0e9df865a69bc02` | `codex/integration-labtools-ui-c2-carryover` | recovery-source-confirmed | not migrated / unknown | scoped plan required | Page style unknown until reconciliation. |
| LabTools | General calculator UI | `ca006ee8a35156e2bb5c396a890942924b4ff99a` | `codex/integration-labtools-ui-c2-carryover` | recovery-source-confirmed | not migrated / unknown | scoped plan required | Do not assume final Figma/new style. |
| LabTools | Reagent preparation UI | `f18b9a0e650fa9bd3cd76cc260ca8e7c145e4bee` | `codex/integration-labtools-ui-c2-carryover` | recovery-source-confirmed | not migrated / unknown | scoped plan required | Needs storage/write audit. |
| LabTools | Western blot loading UI | `a33cffeb0103c47d03bbbe68643ad431482e2ca5` | `codex/integration-labtools-ui-c2-carryover` | recovery-source-confirmed | not migrated / unknown | scoped plan required | Needs page style and runtime audit. |
| LabTools | Boundary pages | `00f4ec6cf68634fb01adb889a9b5041ed16df92c` | `codex/integration-labtools-ui-c2-carryover` | recovery-source-confirmed | not migrated / unknown | scoped plan required | Boundary pages are not runtime completion proof. |
| LabTools | Workbench surface rebuild | `ed396b49e698dcbb28a973cdb7060cd855dcf7b8` | `codex/integration-labtools-ui-c2-carryover` | recovery-source-confirmed | not migrated / unknown | scoped plan required | Current visual surface reference for LabTools. |
| LabTools | Workspace main window wiring | `a4edda1409f95a2ab43ffd435b84f3b9bd4180e4` | `codex/integration-labtools-ui-c2-carryover` | recovery-source-confirmed | not migrated / unknown | scoped plan required | Wiring must be scoped separately from app/labtools migration. |

## Required Next Fields

Before any row can be migrated, add:

- current target branch route status
- file scope
- objectName / handler
- target page
- runtime/service status
- artifact/output status
- test path and result
- page style
- forbidden path check
