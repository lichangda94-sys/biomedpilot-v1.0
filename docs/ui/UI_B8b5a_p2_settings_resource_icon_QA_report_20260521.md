# UI-B8b5a P2 Settings Resource Icon QA Report

Date: 2026-05-21

## 1. QA Scope

This QA report covers only the 13 P2 `settings_resources` icon production candidates generated under:

- `docs/ui/icon_production/p2_settings/svg/`
- `docs/ui/icon_production/p2_settings/png/24/`
- `docs/ui/icon_production/p2_settings/png/32/`
- `docs/ui/icon_production/p2_settings/png/48/`
- `docs/ui/icon_production/p2_settings/png/64/`

No active Settings loader or active asset directory was modified.

## 2. Candidate Inventory

| resource_id | semantic_key | SVG | PNG exports | Semantic QA |
| --- | --- | --- | --- | --- |
| `resource_external_engine` | `settings.page.external_capabilities` | present | 24/32/48/64 present | Category icon only; no installed state |
| `resource_image_analysis_engine` | `settings.page.external_capabilities` | present | 24/32/48/64 present | Category icon only; no enabled state |
| `resource_imagej_fiji` | `settings.page.external_capabilities` | present | 24/32/48/64 present | Settings external capability only; no LabTools first-level entry |
| `resource_pdf_ocr` | `settings.page.external_capabilities` | present | 24/32/48/64 present | OCR category only; no configured/available claim |
| `resource_local_model` | `settings.page.model_engine` | present | 24/32/48/64 present | Local model category only; no model availability claim |
| `resource_cloud_ai` | `settings.page.model_engine` | present | 24/32/48/64 present | Cloud AI category only; no cloud-connected claim |
| `resource_python` | `settings.page.external_capabilities` | present | 24/32/48/64 present | Runtime category only; no installed claim |
| `resource_r` | `settings.page.external_capabilities` | present | 24/32/48/64 present | Runtime category only; no installed claim |
| `resource_go` | `settings.page.analysis_resources` | present | 24/32/48/64 present | GO resource category only; no resource-available claim |
| `resource_kegg` | `settings.page.analysis_resources` | present | 24/32/48/64 present | KEGG resource category only; no resource-available claim |
| `resource_analysis_package` | `settings.page.analysis_resources` | present | 24/32/48/64 present | Package category only; no installed claim |
| `resource_plotting_package` | `settings.page.analysis_resources` | present | 24/32/48/64 present | Plotting package category only; no enabled plotting claim |
| `resource_developer_diagnostics` | `settings.page.developer_diagnostics` | present | 24/32/48/64 present | Developer diagnostics category only; no ordinary-user promotion |

## 3. Visual QA

| Check | Result |
| --- | --- |
| 13 independent SVG files exist | Passed |
| Each SVG uses transparent canvas | Passed |
| SVG files do not embed placeholder PNGs | Passed |
| SVG filenames align with `resource_id` | Passed |
| Each SVG has 24, 32, 48, and 64 px PNG exports | Passed |
| PNG exports are RGBA | Passed |
| PNG exports use transparent canvas | Passed |
| PNG exports are generated under `docs/ui/icon_production/p2_settings/` | Passed |

## 4. Semantic QA

| Risk | QA result |
| --- | --- |
| Icons imply installed / configured / available state | Not observed in candidate files; no checkmarks or success badges were used |
| Cloud AI implies enabled cloud connection | Not observed; icon remains category-level |
| Local model implies model availability | Not observed; icon remains category-level |
| PDF/OCR implies OCR configured or enabled | Not observed; icon remains category-level |
| ImageJ/Fiji enters LabTools first-level IA | Not changed; no active UI wiring was modified |
| Developer diagnostics promoted into ordinary user flow | Not changed; no active Settings UI wiring was modified |

## 5. Boundary QA

| Boundary | Result |
| --- | --- |
| No active Settings resource path under `assets/icons/settings/resources/` | Passed; directory does not exist |
| No `app/**` active loader modification | Passed |
| No `assets/**` active resource modification | Passed |
| No status icon processing | Passed |
| No result/report/export icon processing | Passed |
| No empty-state icon processing | Passed |
| No App icon / Finder icon / `.icns` / iconset / Info.plist / LaunchServices processing | Passed |
| No packaged app build or run | Passed |

## 6. QA Notes

- All 13 resources remain production candidates only.
- `replacement_ready=false` remains required in the manifest.
- `ready_for_pilot_review=true` means the assets are ready for a later review stage, not active UI replacement.
- A later P2 active pilot must still define Settings resource loader behavior, fallback behavior, and detect-first / user-triggered install/update semantics before wiring these assets into active UI.
