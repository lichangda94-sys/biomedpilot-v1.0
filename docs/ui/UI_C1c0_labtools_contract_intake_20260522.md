# UI-C1c0 LabTools Contract Intake for Mockup

日期：2026-05-22

## 1. Scope

This stage carries LabTools contract documents from the LabTools branch into the UIShell documentation tree so UI-C1c LabTools mockup work can use them as formal inputs.

This is a docs-only intake stage.

Not changed:

- `app/**`
- `tests/**`
- `assets/**`
- `scripts/**`
- `dist/**`
- UI runtime
- LabTools backend
- MainLine merge state
- packaging, package smoke, packaged app runtime, LaunchServices, Finder-style launch validation

This stage does not claim LabTools is a complete desktop product.

## 2. Source

Source commit:

```text
063dbdc docs(labtools): define UI integration contract and screen plan
```

Original LabTools document paths:

| Source path | Purpose |
|---|---|
| `/Users/changdali/Developer/biomedpilot v1.0/LabTools/docs/labtools/LabTools_UI_integration_contract_20260522.md` | Public API inventory, API status labels, UI invocation rules. |
| `/Users/changdali/Developer/biomedpilot v1.0/LabTools/docs/labtools/LabTools_screen_inventory_mockup_plan_20260522.md` | Screen inventory, P0 mockup recommendations, screen-level backend bindings. |
| `/Users/changdali/Developer/biomedpilot v1.0/LabTools/docs/labtools/LabTools_backend_gap_audit_20260522.md` | Backend gap audit, feature status matrix, blocked/shell-only boundaries. |

UIShell reference paths:

| UIShell path | Intake status |
|---|---|
| `docs/ui/references/labtools/LabTools_UI_integration_contract_20260522.md` | carried over |
| `docs/ui/references/labtools/LabTools_screen_inventory_mockup_plan_20260522.md` | carried over |
| `docs/ui/references/labtools/LabTools_backend_gap_audit_20260522.md` | carried over |

## 3. Contract Intake Summary

The carried-over LabTools contract updates the previous UI-C1c assumption. UIShell itself still has no active `app/labtools/` runtime adapter, but the LabTools branch now provides a formal backend contract for mockup planning.

For UI-C1c mockups:

- mockup copy may reference the LabTools backend contract as available in the LabTools branch.
- UIShell screens must still display adapter or preview status where runtime integration is not present.
- no mockup should imply that UIShell runtime already calls these APIs.
- no screen should imply packaging or desktop product completion.

## 4. Active UI Mockup Candidates

The following features may enter active UI mockup planning because the LabTools contract marks their backend capability as available or sufficiently defined for UI design:

| Feature | Intake status | Mockup rule |
|---|---|---|
| 通用快速计算 | active UI mockup allowed | Use task-card flow from `QuickCalculatorTaskSpec`; show save/history as adapter-needed where applicable. |
| 动态公式求解 | active UI mockup allowed | Use explicit solve-target segmented controls from `FormulaSpec`; do not rely on blank-field guessing as primary UX. |
| 试剂模板 | active UI mockup allowed | Use template list plus edit side panel; storage path remains adapter-needed. |
| 本次试剂配制 | active UI mockup allowed | Use template -> preparation run -> result -> save record flow; distinguish target volume and suggested volume. |
| WB loading | active UI mockup allowed | Use full WB loading calculation, lane layout, warning/result/status sections. |
| SDS-PAGE | active UI mockup allowed | Use gel template, batch calculation, JSON/XLSX export affordances with file picker adapter. |
| qPCR mix | active UI mockup allowed | Limit to mix calculator; no qPCR analysis or plate result workflow. |
| cell plating | active UI mockup allowed | Limit to cell seeding/plating calculator helper. |
| BCA / OD mockup | mockup allowed with boundary | Use OD matrix, annotations, linear fit warnings; mark save/history/export as backend gap unless record store is added. |

## 5. Shell-only, Mockup-only, and Blocked Areas

| Feature | Required status in UI-C1c | Reason |
|---|---|---|
| ELISA true analysis | `blocked_until_backend` | `labtools.elisa` is an empty namespace; no ELISA MVP API exists. |
| 细胞实验记录真实保存 | `blocked_until_backend` | Cell culture currently exposes cell seeding only; no record model/store exists. |
| ImageJ/Fiji automatic image analysis | `shell_only` | No LabTools ImageJ/Fiji backend API, runner, ROI model, or result parser exists. |
| all calculations have history | `mockup_only` / `blocked_until_backend` | Generic `CalculationRecord` exists, but no unified `CalculationRecordStore` exists. |
| all pages have file export | `mockup_only` | WB and SDS-PAGE have partial export support; many pages do not. |
| LabTools complete desktop productization | forbidden claim | Current work is contract/mockup planning, not runtime implementation or packaged validation. |

## 6. UI-C1c Mockup Allowed Capability List

UI-C1c mockup prompts may use:

- 通用快速计算
- 动态公式求解
- 试剂模板
- 本次试剂配制
- WB loading
- SDS-PAGE
- qPCR mix
- cell plating
- BCA / OD mockup

Allowed interaction language:

- backend-ready in LabTools branch
- adapter needed in UIShell
- local-only record/store planned where a store exists but UIShell path adapter is not wired
- mockup-only where a backend record/export layer is missing

## 7. UI-C1c Forbidden / Non-misleading Claims

UI-C1c mockups must not imply:

- ELISA 真实分析已完成
- 细胞实验记录真实保存已完成
- ImageJ/Fiji 自动图像分析已完成
- 所有计算都有历史记录
- 所有页面都有文件导出
- LabTools 已完整桌面产品化
- UIShell runtime already imports or executes LabTools branch APIs
- MainLine has merged LabTools UI runtime
- packaging, package smoke, or packaged app validation has been performed in this stage

## 8. Gaps Required Before Real Runtime Integration

Before UI-C2 implementation from approved mockups, the following gaps must be explicitly resolved or gated:

| Gap | Required before |
|---|---|
| BioMedPilot storage root adapter for LabTools stores | Any real save/history workflow |
| UI-facing error/warning/result view model | Any runtime calculator page |
| function binding layer from `calculator_name` / `solver_name` to actual Python calls | Quick calculator and formula solver runtime |
| generic `CalculationRecordStore` | Quick calculator and dynamic formula history |
| BCA record model/store/export | BCA / OD true save/history/export |
| SDS-PAGE persistent template store | SDS-PAGE template library beyond import/export files |
| file picker adapter for export APIs | WB Markdown/CSV, SDS-PAGE XLSX/JSON |
| ELISA MVP backend | ELISA real analysis screen |
| cell experiment record model/store | Cell record true save/history |
| ImageJ/Fiji external engine adapter | Any image analysis beyond Settings/status callout |

## 9. Next-stage Recommendations

### UI-C1c1 LabTools P0 wireframe prompts

Generate low-to-mid fidelity wireframe prompts using the carried-over contract references.

Recommended P0 prompt groups:

- LabTools home with status badges and module entry cards.
- General quick calculator with task cards and result/warning panel.
- Dynamic formula solver with formula list, solve-target segmented controls, and trace/result panel.
- Reagent templates list plus edit side panel.
- Reagent preparation run flow.
- WB loading calculator with sample table and lane layout.
- SDS-PAGE gel preparation with template editor and result table.
- BCA / OD record mockup with explicit testing/mockup boundary.
- Cell experiment record template home as shell-only with cell plating helper link.

### UI-C1c2 LabTools high-fidelity mockup prompts

Convert approved P0 wireframes into high-fidelity desktop mockup prompts.

High-fidelity prompts must preserve:

- adapter-needed badges
- mockup-only labels
- blocked/shell-only boundaries
- review/warning blocks
- disabled export states where backend is not available
- no productization claims

### UI-C2 LabTools implementation from approved mockups

Implementation should start only after mockups are approved and runtime gaps are assigned.

Recommended implementation order:

1. LabTools home shell and navigation only.
2. Storage adapter design for LabTools stores.
3. Quick calculator and formula solver adapter.
4. Reagent template and preparation workflow.
5. WB loading and SDS-PAGE.
6. BCA / OD only after record/export gap is resolved.
7. ELISA, cell records, and ImageJ/Fiji remain blocked until backend MVPs or adapters exist.

## 10. Verification

Required verification for this docs-only intake:

```bash
git diff --check
git diff --cached --check
```

Not run by design:

- package smoke
- packaged app
- LaunchServices / Finder-style launch
- UI runtime
- LabTools backend tests
