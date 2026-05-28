# UI-B8b.1 Icon Board Intake and Asset Extraction Plan

## 1. Scope

- Date: 2026-05-21
- Source folder: `/Users/changdali/Desktop/UI/界面示意图/icon`
- Inventory: `docs/ui/resource_inventory/UI_B8b_icon_asset_plan_20260521.csv`
- Purpose: intake the five non-App-icon design boards, map each planned icon to semantic keys and future asset paths, and define extraction/replacement gates.

This stage is intake and planning only. It does not cut icons into active assets, does not replace existing icons, does not modify loaders, does not touch App icon/Finder icon/`.icns`/iconset/Info.plist/LaunchServices, does not package, does not run packaged app, and does not overwrite any desktop app.

## 2. Source Boards Found

| board | file | detected_size | alpha | scope |
|---|---|---:|---|---|
| board_01_modules_status | `/Users/changdali/Desktop/UI/界面示意图/icon/4 个模块图标 + 10 个状态图标.png` | 1536 x 1024 | no, RGB | Module icons and status icons. |
| board_02_settings_resources | `/Users/changdali/Desktop/UI/界面示意图/icon/Settings 外部资源图标.png` | 1536 x 1024 | no, RGB | Settings external/resource icons. |
| board_03_labtools | `/Users/changdali/Desktop/UI/界面示意图/icon/LabTools 8 个核心图标板.png` | 1536 x 1024 | no, RGB | LabTools icon family. |
| board_04_result_report_export | `/Users/changdali/Desktop/UI/界面示意图/icon/Result : Report : Export 图标.png` | 1536 x 1024 | no, RGB | Result, Report and Export icon family. |
| board_05_bio_meta_empty | `/Users/changdali/Desktop/UI/界面示意图/icon/Bio : Meta 页面图标与 Empty States.png` | 1536 x 1024 | no, RGB | Bio page icons, Meta page icons and empty states. |

## 3. Intake Conclusion

The five boards are suitable as visual reference and as a possible source for temporary cropped PNG placeholders. They are not suitable as final production resources by themselves because each board is one RGB bitmap without per-icon transparent/vector source. Final replacement should use vector redraw or designer-exported per-icon SVG plus PNG size exports.

Therefore the inventory uses these default gates:

- `can_extract_from_board=true` for board-contained non-App icons, meaning a later stage can crop temporary PNGs if explicitly authorized.
- `needs_vector_redraw=true` for all board-contained icons, because final assets need clean transparent/vector sources.
- `replacement_allowed_now=false` for all rows.
- `replacement_gate=UI-B8b2 extraction QA + vector redraw + focused loader tests` for non-App icons.
- `replacement_gate=UI-B10 only` for App icon / Finder icon / Info.plist / LaunchServices.

## 4. Extraction Strategy

1. Preserve source boards unchanged.
2. If a future extraction stage is authorized, create a scratch folder such as `docs/ui/icon_extraction/batch_01/` for cropped references.
3. Crop each icon with padding and consistent square canvas.
4. Export temporary PNG references at `24`, `32`, `48`, and `64` px only as placeholders.
5. Mark every cropped bitmap as placeholder, never final.
6. For production replacement, redraw/export each icon from vector source to the target SVG and PNG paths listed in the inventory.
7. Only after complete family review should active loaders be changed in a separate implementation stage.

## 5. Future Target Paths

The CSV lists future paths only. This UI-B8b.1 stage does not create or populate these folders:

```text
assets/icons/modules/
assets/icons/status/
assets/icons/settings/resources/
assets/icons/labtools/
assets/icons/result_report_export/
assets/icons/bioinformatics/pages/
assets/icons/meta/pages/
assets/images/empty_states/
```

## 6. Replacement Boundaries

| boundary | rule |
|---|---|
| Active resources | Do not replace active icons in this stage. |
| App icon | App icon, Finder icon, `.icns`, iconset, Info.plist binding and LaunchServices remain deferred to UI-B10. |
| Board crop quality | If an icon cannot be cleanly isolated from the board, mark `can_extract_from_board=false` and keep `needs_vector_redraw=true`. |
| Temporary PNG | Cropped PNGs are placeholder references only, not final assets. |
| Semantic keys | Icons must support existing `moduleKey`, `pageKey`, `statusKey`, `resource.status`, `analysis.status`, `report.status` and `export.format` semantics. |
| Product claims | Status and report/export icons must not imply production readiness, formal analysis, report-ready package, automatic install/update or cloud configuration. |

## 7. Board-Specific Notes

### 7.1 Modules and Status

Module icons can later support Dashboard, Sidebar and module home surfaces. Status icons must remain subordinate to visible text labels. `testing`, `planned`, `shell_only`, `developer_preview`, `blocked`, `available`, `not_configured`, `failed`, `preflight_only` and `draft` cannot be styled as completed production states.

### 7.2 Settings Resources

Settings resource icons must preserve detect-first and user-triggered install/update semantics. ImageJ/Fiji belongs to Settings external image engine configuration, not LabTools primary IA. Cloud AI cannot imply an enabled cloud configuration.

### 7.3 LabTools

The LabTools family covers the three primary entries and five experiment categories. It must not turn ImageJ/Fiji into a LabTools first-level entry and must not mix WB/PCR/ELISA/MTT/BCA/SDS-PAGE into generic calculator identity.

### 7.4 Result / Report / Export

Result/report/export icons must preserve empty result, draft report and export gating. PDF/Excel/CSV/archive/share visuals are future format markers only and do not authorize report-ready package generation.

### 7.5 Bio / Meta Pages and Empty States

Bio and Meta page icons should align to current target IA keys, not old UI numbering. Empty states should be compact operational illustrations and must not hide blocked/preflight/shell-only semantics.

## 8. Verification

Commands run:

| command | result |
|---|---|
| `find /Users/changdali/Desktop/UI/界面示意图/icon -maxdepth 2 -type f -print \| sort` | Found five icon board PNG files. |
| `file /Users/changdali/Desktop/UI/界面示意图/icon/*` | All five boards are 1536 x 1024 RGB PNG files. |
| CSV parse check for `docs/ui/resource_inventory/UI_B8b_icon_asset_plan_20260521.csv` | Passed: 75 rows, required fields present, `replacement_allowed_now=false` for all rows. |
| `git diff --check` | Passed. |
| `git diff --cached --check` | Passed. |

`git diff --check` and `git diff --cached --check` are recorded after staging in the handoff for this stage.

## 9. No Active Asset Change Statement

This stage only adds a planning document and CSV inventory under `docs/ui`. It does not modify `app/**`, `tests/**`, `assets/**`, scripts, dist, packaged app files or desktop entries.
