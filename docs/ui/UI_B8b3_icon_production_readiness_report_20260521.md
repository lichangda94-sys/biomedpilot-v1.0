# UI-B8b3 Icon Production Readiness Report

Date: 2026-05-21

## 1. Scope

UI-B8b3 establishes the formal icon resource readiness layer from the UI-B8b2 placeholder extraction outputs. It prepares the replacement matrix, production export rules, vector redraw requirements, and read-only inventory guard tests.

Inputs:

- `docs/ui/icon_extraction/UI_B8b2_icon_extraction_manifest_20260521.csv`
- `docs/ui/UI_B8b2_icon_extraction_QA_report_20260521.md`
- `docs/ui/resource_inventory/UI_B8b_icon_asset_plan_20260521.csv`
- `docs/ui/icon_extraction/batch_01/`

## 2. Boundary Statement

This stage did not replace active UI resources. Placeholder PNGs remain under `docs/ui/icon_extraction/batch_01/` and were not moved into `assets/icons/` or `assets/images/`.

No `app/**` active UI code was modified. No active loader was modified. App icon, Finder icon, `.icns`, iconset, `Info.plist`, LaunchServices, packaged apps, and desktop app entries remain untouched and deferred to UI-B10.

## 3. Outputs

| Output | Path | Status |
| --- | --- | --- |
| Replacement readiness matrix | `docs/ui/resource_inventory/UI_B8b3_icon_replacement_readiness_matrix_20260521.csv` | Created |
| Production readiness report | `docs/ui/UI_B8b3_icon_production_readiness_report_20260521.md` | Created |
| Vector redraw brief | `docs/ui/UI_B8b3_vector_redraw_brief_20260521.md` | Created |
| Read-only inventory test | `tests/ui/test_icon_resource_readiness_inventory.py` | Created |

## 4. Replacement Readiness Matrix Summary

| Field | Result |
| --- | --- |
| Matrix rows | 74 |
| `replacement_ready` | `false` for all rows |
| Placeholder reference location | `docs/ui/icon_extraction/batch_01/` |
| Final SVG target type | Future `assets/icons/**` or `assets/images/**` path only |
| Active replacement | None |

Priority distribution:

| Priority | Families | Count |
| --- | --- | ---: |
| P1 | `modules`, `labtools`, `bio_pages`, `meta_pages` | 31 |
| P2 | `settings_resources` | 13 |
| P3 | `result_report_export`, `empty_states` | 20 |
| P4 | `status` | 10 |

Family distribution:

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

## 5. Semantic Key Reuse

Some semantic keys are intentionally reused across related resources, such as a status badge and its matching empty-state illustration. The matrix records `semantic_reuse_reason` for these groups so future tests can distinguish intentional reuse from accidental collisions.

Examples:

| semantic_key | reuse reason |
| --- | --- |
| `feature.status.blocked` | Shared by blocked status icon and blocked empty-state illustration. |
| `feature.status.shell_only` | Shared by shell-only status icon and shell-only empty-state illustration. |
| `analysis.status.preflight_only` | Shared by preflight-only status icon and preflight-only empty-state illustration. |
| `report.export_panel` | Shared by multiple gated report/export action icons. |
| `settings.page.external_capabilities` | Shared by external capability resources within one Settings page group. |

## 6. Formal Resource Export Specification

| Rule | Requirement |
| --- | --- |
| Primary source | SVG is the authoritative final resource format. |
| PNG exports | 24, 32, 48, and 64 px. |
| Background | Transparent. No board card background, no white matte, no baked page backdrop. |
| Canvas | Square canvas for icons. Empty-state illustrations may use square source art with final layout sizing handled by UI. |
| Padding | Keep visual glyph inside a stable safe area; do not crop shadows or strokes. |
| Stroke | Use consistent stroke weight within each family and avoid hairlines that disappear at 24 px. |
| Corners | Use consistent corner radius for document, panel, card, and chip motifs. |
| Shadows | Avoid baked heavy shadows in final SVG. Use only subtle, token-compatible shadow if product style requires it. |
| Light/dark readability | Every icon must remain readable on light background and dark shell surfaces. |
| Naming | Use `resource_id` as the filename stem. SVG path equals `required_final_svg_path`; PNG exports equal `required_png_exports`. |
| Status safety | Status icons must not make `testing`, `planned`, `shell_only`, `developer_preview`, `blocked`, `preflight_only`, or `draft` look completed. |

## 7. Replacement Gates

| Gate | Requirement |
| --- | --- |
| Vector source | Final SVG or clean source export exists for the resource. |
| Visual QA | Light/dark readability, padding, stroke, and family consistency reviewed. |
| Semantic QA | Icon meaning matches `semantic_key` and does not imply unavailable production capability. |
| Loader test | Focused resource-loader tests pass before any active path is wired. |
| Status review | P4 status icons require separate status semantic review before replacement. |
| Result/export review | P3 report/export icons require Result / Report / Export gating review before active usage. |

## 8. Special Guardrails

- Result / Report / Export icons remain resource-preparation only and do not enable active affordances.
- `resource_imagej_fiji`, `resource_cloud_ai`, `resource_local_model`, and `resource_pdf_ocr` must preserve detect-first and user-triggered semantics.
- App icon, Finder icon, `.icns`, iconset, `Info.plist` binding, LaunchServices, and desktop app identity stay deferred to UI-B10.
- Placeholder PNGs remain documentation QA artifacts and must not be copied into active asset directories.

## 9. Read-Only Audit Test

Added:

`tests/ui/test_icon_resource_readiness_inventory.py`

The test checks:

- `resource_id` uniqueness.
- planned target path uniqueness.
- required final SVG path uniqueness.
- semantic key duplicates require explicit reuse reasons.
- all rows remain `replacement_ready=false`.
- status and Result / Report / Export resources remain non-ready.
- App icon remains `UI-B10 only`.

The test does not import or exercise the active UI loader.

## 10. Commands And Results

| Command | Result |
| --- | --- |
| Python parse of UI-B8b2 manifest and UI-B8b plan | Confirmed 74 extracted manifest rows and 75 inventory rows. |
| Python generation of readiness matrix | Created 74 matrix rows. |
| `python3 -m pytest -q tests/ui/test_icon_resource_readiness_inventory.py` | Passed: `5 passed in 0.12s`. |
| `git diff --check` | Passed. |
| `git diff --cached --check` | Passed after staging UI-B8b3 docs, matrix, and read-only audit test. |

## 11. Current Readiness Conclusion

The 74 non App-icon resources are organized enough to enter formal vector redraw or Figma component production, but none is ready for active replacement. The next production step should create clean SVG sources and regenerated transparent PNG exports while keeping active loader wiring out of scope until a later replacement stage.
