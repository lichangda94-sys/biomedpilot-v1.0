# LabTools Reconciliation Ledger

Date: 2026-05-29

Purpose: absorb LabTools findings from `docs/ui/UI线路既往检查.md` into Project Control without migrating code.

## Governing Notes

- LabTools currently has pages in the accepted packaged preview, but those pages may be older UI pages.
- Each page must be classified as one of: `figma/new`, `old`, `hybrid`, `placeholder`, `missing`, `unknown`.
- Do not migrate whole `app/labtools/**`.
- Do not treat preview presence as proof of final UI style or runtime readiness.
- Do not touch `project_storage/` during reconciliation.

## Initial Ledger

| Feature / Page | Historical Commit | Source | Expected Files From Historical Check | Page Style | Runtime Status | Test Status | MainLine Status | Migration Method | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LabTools navigation shell | `3bf79f4fa36a099b2442ebcdc0e9df865a69bc02` | `codex/integration-labtools-ui-c2-carryover` | `app/labtools/workspace.py`; `assets/icons/labtools/*` | unknown | unknown | unknown | not migrated / unknown | scoped plan required | Initial route shell source. |
| General calculator UI | `ca006ee8a35156e2bb5c396a890942924b4ff99a` | `codex/integration-labtools-ui-c2-carryover` | `app/labtools/labtools_home.py`; `app/labtools/workspace.py` | unknown | unknown | unknown | not migrated / unknown | scoped plan required | Must determine whether preview page is old, hybrid, or figma/new. |
| Reagent preparation UI | `f18b9a0e650fa9bd3cd76cc260ca8e7c145e4bee` | `codex/integration-labtools-ui-c2-carryover` | `app/labtools/labtools_home.py`; `app/labtools/workspace.py` | unknown | unknown | unknown | not migrated / unknown | scoped plan required | Requires storage/write boundary check. |
| Western blot loading UI | `a33cffeb0103c47d03bbbe68643ad431482e2ca5` | `codex/integration-labtools-ui-c2-carryover` | `app/labtools/labtools_home.py`; `app/labtools/workspace.py` | unknown | unknown | unknown | not migrated / unknown | scoped plan required | Needs page style and WB runtime audit. |
| LabTools boundary pages | `00f4ec6cf68634fb01adb889a9b5041ed16df92c` | `codex/integration-labtools-ui-c2-carryover` | `app/labtools/workspace.py` | unknown | boundary-only / unknown | unknown | not migrated / unknown | scoped plan required | Boundary pages must not be counted as completed runtime. |
| Storage adapter skeleton | `edfa2a595b5b4d249cd91fa9aa1420904e7f8df0` | `codex/integration-labtools-ui-c2-carryover` | `app/labtools_storage_adapter.py` | n/a | unknown | unknown | not migrated / unknown | scoped plan required | Interface source only; not whole app/labtools migration permission. |
| Local data store read paths | `7afe07bb5a07225bddf43ed1ecc3201ac4443ebf` | `codex/integration-labtools-ui-c2-carryover` | `app/labtools_runtime.py`; `app/labtools_storage_adapter.py` | n/a | unknown | unknown | not migrated / unknown | scoped plan required | Read path integration must be validated independently. |
| Local reagent write UI integration | `e64454be34d4dc0ea37c68b06c2f889138ccedf9` | `codex/integration-labtools-ui-c2-carryover` | `app/labtools_runtime.py`; `app/labtools_storage_adapter.py` | n/a | unknown | unknown | not migrated / unknown | scoped plan required | Write behavior requires explicit approval and tests before migration. |
| Local sample write UI integration | `b40cc8df0683c78019375a2f6dbd2b68ce4d35b9` | `codex/integration-labtools-ui-c2-carryover` | `app/labtools_runtime.py`; `app/labtools_storage_adapter.py` | n/a | unknown | unknown | not migrated / unknown | scoped plan required | Write behavior requires explicit approval and tests before migration. |
| LabTools Workbench surface rebuild | `ed396b49e698dcbb28a973cdb7060cd855dcf7b8` | `codex/integration-labtools-ui-c2-carryover` | `app/labtools/labtools_home.py`; `app/labtools/workspace.py`; `assets/icons/labtools/*` | unknown | unknown | unknown | not migrated / unknown | scoped plan required | Visual reference, not migration authorization. |
| LabTools LAN release increment | `44885c50b17b0c0646074f7a20cfc48f91dc2dc3` | `codex/integration-labtools-ui-c2-carryover` | needs scoped file audit | n/a | unknown | unknown | not migrated / unknown | scoped plan required | Merge commit; do not replay without conflict plan. |
| LabTools workspace main window wiring | `a4edda1409f95a2ab43ffd435b84f3b9bd4180e4` | `codex/integration-labtools-ui-c2-carryover` | `app/shell/main_window.py`; `app/labtools/workspace.py` | n/a | route wiring unknown | unknown | not migrated / unknown | scoped plan required | Wiring must be scoped separately from `app/labtools/**`. |

## Required Page Style Audit

Each LabTools page must be classified before migration:

| Page Style | Meaning |
| --- | --- |
| `figma/new` | Matches accepted new UI/Figma-style page after evidence review. |
| `old` | Legacy page; may be useful but not final UI. |
| `hybrid` | New shell wrapping older content. |
| `placeholder` | Placeholder surface without complete feature path. |
| `missing` | No target page. |
| `unknown` | Not yet audited. |

## Migration Boundary

`app/labtools/**` must not be moved as a whole tree. Any LabTools recovery must name exact files, page route, handler, runtime/service, tests, and forbidden path result.
