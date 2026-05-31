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

## Historical Recovery Sources

Source: `docs/ui/UI线路既往检查.md`. These rows identify where LabTools page/interface recovery evidence lives. They do not replace the ledger above; page style, runtime status, tests, and priority must still be filled using the Integration audit structure.

| Feature / Page | Historical Commit | Source | Expected Files From Historical Check | Page Style | Runtime Status | Test Status | Migration Priority | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LabTools navigation shell | `3bf79f4fa36a099b2442ebcdc0e9df865a69bc02` | `codex/integration-labtools-ui-c2-carryover` | `app/labtools/workspace.py`; `assets/icons/labtools/*` | unknown | unknown | unknown | needs audit | Initial route shell source. |
| General calculator UI | `ca006ee8a35156e2bb5c396a890942924b4ff99a` | `codex/integration-labtools-ui-c2-carryover` | `app/labtools/labtools_home.py`; `app/labtools/workspace.py` | unknown | unknown | unknown | needs audit | Determine whether page is old, hybrid, or figma/new. |
| Reagent preparation UI | `f18b9a0e650fa9bd3cd76cc260ca8e7c145e4bee` | `codex/integration-labtools-ui-c2-carryover` | `app/labtools/labtools_home.py`; `app/labtools/workspace.py` | unknown | unknown | unknown | needs audit | Requires storage/write boundary check. |
| Western blot loading UI | `a33cffeb0103c47d03bbbe68643ad431482e2ca5` | `codex/integration-labtools-ui-c2-carryover` | `app/labtools/labtools_home.py`; `app/labtools/workspace.py` | unknown | unknown | unknown | needs audit | Needs page style and WB runtime audit. |
| LabTools boundary pages | `00f4ec6cf68634fb01adb889a9b5041ed16df92c` | `codex/integration-labtools-ui-c2-carryover` | `app/labtools/workspace.py` | unknown | boundary-only / unknown | unknown | needs audit | Boundary pages must not be counted as completed runtime. |
| Storage adapter skeleton | `edfa2a595b5b4d249cd91fa9aa1420904e7f8df0` | `codex/integration-labtools-ui-c2-carryover` | `app/labtools_storage_adapter.py` | n/a | unknown | unknown | needs audit | Interface source only; not whole-tree migration permission. |
| Local data store read paths | `7afe07bb5a07225bddf43ed1ecc3201ac4443ebf` | `codex/integration-labtools-ui-c2-carryover` | `app/labtools_runtime.py`; `app/labtools_storage_adapter.py` | n/a | unknown | unknown | needs audit | Read path integration must be validated independently. |
| Local reagent write UI integration | `e64454be34d4dc0ea37c68b06c2f889138ccedf9` | `codex/integration-labtools-ui-c2-carryover` | `app/labtools_runtime.py`; `app/labtools_storage_adapter.py` | n/a | unknown | unknown | needs audit | Write behavior requires explicit tests before migration. |
| Local sample write UI integration | `b40cc8df0683c78019375a2f6dbd2b68ce4d35b9` | `codex/integration-labtools-ui-c2-carryover` | `app/labtools_runtime.py`; `app/labtools_storage_adapter.py` | n/a | unknown | unknown | needs audit | Write behavior requires explicit tests before migration. |
| LabTools Workbench surface rebuild | `ed396b49e698dcbb28a973cdb7060cd855dcf7b8` | `codex/integration-labtools-ui-c2-carryover` | `app/labtools/labtools_home.py`; `app/labtools/workspace.py`; `assets/icons/labtools/*` | unknown | unknown | unknown | needs audit | Visual reference, not migration authorization. |
| LabTools LAN release increment | `44885c50b17b0c0646074f7a20cfc48f91dc2dc3` | `codex/integration-labtools-ui-c2-carryover` | needs scoped file audit | n/a | unknown | unknown | needs audit | Merge commit; do not replay without conflict plan. |
| LabTools workspace main window wiring | `a4edda1409f95a2ab43ffd435b84f3b9bd4180e4` | `codex/integration-labtools-ui-c2-carryover` | `app/shell/main_window.py`; `app/labtools/workspace.py` | n/a | route wiring unknown | unknown | needs audit | Wiring must be scoped separately from `app/labtools/**`. |
