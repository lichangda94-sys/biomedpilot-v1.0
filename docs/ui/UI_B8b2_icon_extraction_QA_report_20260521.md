# UI-B8b2 Icon Extraction QA Report

Date: 2026-05-21

## 1. Scope

This stage audits and extracts temporary placeholder PNGs from the five non App-icon boards under:

`/Users/changdali/Desktop/UI/界面示意图/icon`

The extraction follows:

`docs/ui/resource_inventory/UI_B8b_icon_asset_plan_20260521.csv`

This stage does not replace active UI resources and does not modify app loaders, App icon bindings, Finder icon resources, `.icns`, iconsets, `Info.plist`, LaunchServices, packaged apps, or desktop app entries.

## 2. Outputs

| Output | Path | Status |
| --- | --- | --- |
| Placeholder PNG directory | `docs/ui/icon_extraction/batch_01/` | Created |
| Extraction manifest | `docs/ui/icon_extraction/UI_B8b2_icon_extraction_manifest_20260521.csv` | Created |
| QA report | `docs/ui/UI_B8b2_icon_extraction_QA_report_20260521.md` | Created |

## 3. Extraction Summary

| Item | Count |
| --- | ---: |
| Inventory rows | 75 |
| Extractable non App-icon rows | 74 |
| Deferred rows | 1 |
| Placeholder PNGs exported | 296 |
| Export sizes per resource | 24, 32, 48, 64 px |

Deferred row:

| resource_id | reason |
| --- | --- |
| `app_icon_deferred` | App icon, Finder icon, `.icns`, iconset, Info.plist icon binding, LaunchServices, and desktop app resources remain deferred to UI-B10. |

Extracted resource families:

| resource_family | Count |
| --- | ---: |
| `modules` | 4 |
| `status` | 10 |
| `settings_resources` | 13 |
| `labtools` | 8 |
| `result_report_export` | 14 |
| `bio_pages` | 9 |
| `meta_pages` | 10 |
| `empty_states` | 6 |

## 4. Extraction Method

The five boards are RGB PNG boards at `1536 x 1024`. The extraction used manual board-aware crop boxes, square output canvases, and near-white background alpha removal. Each extractable row produced four placeholder PNGs under `docs/ui/icon_extraction/batch_01/`.

All manifest rows are explicitly marked:

| Field | Value |
| --- | --- |
| `placeholder_only` | `true` |
| `needs_vector_redraw` | `true` |
| `replacement_allowed_now` | `false` |

## 5. Clean Placeholder Crops

The following families are usable for QA review as temporary placeholder crops:

| resource_family | QA status |
| --- | --- |
| `modules` | Usable as placeholder only; includes board glow, hex or circular backgrounds, and soft shadows. |
| `status` | Usable as placeholder only; status meaning must stay tied to semantic keys, not visual optimism. |
| `settings_resources` | Usable as placeholder only; external resource meanings require future visual consistency pass. |
| `labtools` | Usable as placeholder only; lab category icons are visually readable but not final. |
| `result_report_export` | Usable as placeholder only; report/export icons need gating review before active UI usage. |
| `bio_pages` | Usable as placeholder only; green Bio page icons remain board-derived crops. |
| `meta_pages` | Usable as placeholder only after sample QA crop correction. |
| `empty_states` | Usable as placeholder only; larger empty-state illustrations need final vector or illustration treatment. |

## 6. Crop QA Findings

| Finding | Affected resources | Severity | Resolution |
| --- | --- | --- | --- |
| RGB boards do not provide per-icon transparent source artwork. | All 74 extracted resources | Medium | Keep as placeholder PNG only; redraw as SVG or clean source PNG before active replacement. |
| Soft backgrounds, shadows, antialiasing, and board glow remain visible. | All 74 extracted resources | Medium | Mark `needs_vector_redraw=true`; do not treat as final assets. |
| Dense Meta row required crop correction during sample QA. | 10 `meta_pages` resources | Medium | Re-cropped Meta row with tighter icon-centered boxes and recorded `placeholder_ok_corrected_crop_soft_background`. |
| Some 24 px outputs lose small detail. | `settings_resources`, `result_report_export`, `empty_states` | Low | Keep for QA only; final resources need pixel-fitting or vector export. |
| Empty-state illustrations are larger than normal icon primitives. | 6 `empty_states` resources | Low | Treat as empty-state placeholder illustrations, not small active icons. |

## 7. Semantic QA Findings

No active UI replacement was performed, so there is no runtime semantic change. The following resources still need careful gating before any future active use:

| Resource group | Risk | Required rule |
| --- | --- | --- |
| Status icons | `testing`, `planned`, `shell_only`, `developer_preview`, `blocked`, `preflight_only`, and `draft` must not appear visually equivalent to final or completed states. | Bind future active usage to `feature.status`, `analysis.status`, `resource.status`, and `report.status` semantic keys. |
| `report_generate`, `export_result`, `export_pdf`, `export_excel`, `export_csv`, `export_archive`, `share_result` | Could imply report-ready or export-ready capability. | Keep behind Result / Report / Export gating until backend and report boundaries allow. |
| `resource_cloud_ai`, `resource_local_model`, `resource_pdf_ocr`, `resource_imagej_fiji` | Could imply configured external capability. | Keep detect-first and user-triggered configuration language. |
| `empty_result` | Could imply a real computed result is missing. | Distinguish `testing_summary_only`, `draft`, and formal computed result states. |

## 8. Must Vector Redraw

All 74 extracted resources must be vector redrawn or exported from a clean source before active replacement. None of the current placeholder PNGs should be moved into `assets/icons/`, `assets/images/`, or any active loader path.

## 9. Not Recommended For Replacement Now

| Scope | Recommendation |
| --- | --- |
| All 74 extracted resources | Do not replace active UI assets now. Keep only under `docs/ui/icon_extraction/batch_01/`. |
| App icon / Finder icon / Info.plist icon binding / LaunchServices | Do not touch in UI-B8b2. Defer to UI-B10. |
| Result / Report / Export icons | Do not use as active affordances until gating and report-ready boundaries are verified. |
| Status icons | Do not use without semantic status key binding and visual state review. |
| Empty states | Do not use as final illustrations; redraw or produce clean source assets first. |

## 10. Manifest Schema

The manifest records:

`resource_id / semantic_key / resource_family / source_board / source_board_path / target_future_path / crop_box / export_paths / needs_vector_redraw / placeholder_only / replacement_allowed_now / qa_status / qa_notes`

`target_future_path` is intentionally a future target reference only. It is not an active replacement path in this stage.

## 11. Commands And Results

| Command | Result |
| --- | --- |
| `file /Users/changdali/Desktop/UI/界面示意图/icon/*.png` | Confirmed five source boards are PNG images, each `1536 x 1024`, RGB. |
| Python inventory parse for `docs/ui/resource_inventory/UI_B8b_icon_asset_plan_20260521.csv` | `inventory_rows=75`, `extractable_rows=74`, deferred row `app_icon_deferred`. |
| Python extraction script | Created `74` manifest rows and `296` placeholder PNG files. |
| Sample image QA with local image viewer | Found Meta row right-edge crop issue; corrected all 10 `meta_pages` crop boxes. |
| Intermediate Python manifest update | Failed with `ValueError` because the script used `notes` instead of manifest column `qa_notes`; manifest was reconstructed from inventory and final verification passed. |
| Final Python manifest verification | `manifest_rows=74`, `png_files=296`, `missing_exports=0`, `placeholder_only=['true']`, `needs_vector_redraw=['true']`, `replacement_allowed_now=['false']`. |
| `git diff --check` | Passed. |
| `git diff --cached --check` | Passed after staging the UI-B8b2 documentation and placeholder extraction artifacts. |

## 12. Boundary Confirmation

- No `app/**` files were modified.
- No `tests/**` files were modified.
- No `assets/**` active resources were modified.
- No active loader was modified.
- No App icon, Finder icon, `.icns`, iconset, `Info.plist`, LaunchServices, packaged app, or desktop entry was modified.
- No packaged app was run.
- No icon was marked as final.
- No status resource was promoted to a formal completed state.
