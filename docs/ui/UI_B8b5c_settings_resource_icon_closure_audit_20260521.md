# UI-B8b5c Settings Resource Icon Closure Audit

Date: 2026-05-21

## 1. Audit Scope

UI-B8b5c closes the P2 Settings resource icon sequence by auditing:

- UI-B8b5a production candidate assets
- UI-B8b5b active pilot assets
- Settings resource registry / loader
- Settings shell wiring
- fallback behavior
- detect-first / user-triggered boundaries
- test coverage
- unprocessed icon families

This is a closure audit. It does not activate any additional icons and does not modify Settings behavior.

## 2. Inputs Read

| Input | Status |
| --- | --- |
| `docs/ui/icon_production/UI_B8b5a_p2_settings_resource_icon_production_manifest_20260521.csv` | Read |
| `docs/ui/UI_B8b5a_p2_settings_resource_icon_final_asset_production_report_20260521.md` | Read |
| `docs/ui/UI_B8b5a_p2_settings_resource_icon_QA_report_20260521.md` | Read |
| `docs/ui/UI_B8b5b_p2_settings_resource_icon_active_pilot_manifest_20260521.csv` | Read |
| `docs/ui/UI_B8b5b_p2_settings_resource_icon_replacement_pilot_20260521.md` | Read |
| `docs/ui/UI_B8b4d_p1_active_icon_pilot_closure_audit_20260521.md` | Read as prior-stage boundary context |
| `app/app_identity.py` | Read by search for registry and loader |
| `app/shell/main_window.py` | Read by search for Settings shell wiring |
| `tests/ui/test_p2_settings_resource_icon_production_manifest.py` | Read and rerun |
| `tests/ui/test_p2_settings_resource_icon_active_pilot.py` | Read and rerun |

## 3. Resource Closure Summary

| Stage | Resource family | Rows | SVG | PNG exports | Active replacement | Closure status |
| --- | --- | ---: | ---: | ---: | --- | --- |
| UI-B8b5a | `settings_resources` | 13 | 13 docs-only candidates | 52 docs-only candidates | No | Closed as production candidate |
| UI-B8b5b | `settings_resources` | 13 | 13 active pilot SVGs | 52 active pilot PNGs | Pilot only | Closed as active pilot |

Active pilot directory:

- `assets/icons/settings/resources/`

Active pilot count:

- 65 files total
- 13 SVG files
- 52 PNG exports

## 4. Resource Inventory

| resource_id | semantic_key | Active status | Semantic closure |
| --- | --- | --- | --- |
| `resource_external_engine` | `settings.page.external_capabilities` | active pilot | Category marker only |
| `resource_image_analysis_engine` | `settings.page.external_capabilities` | active pilot | Category marker only |
| `resource_imagej_fiji` | `settings.page.external_capabilities` | active pilot | Settings external image engine only; not LabTools first-level IA |
| `resource_pdf_ocr` | `settings.page.external_capabilities` | active pilot | OCR resource category only; not runnable OCR |
| `resource_local_model` | `settings.page.model_engine` | active pilot | Model category only; not inference-ready |
| `resource_cloud_ai` | `settings.page.model_engine` | active pilot | Cloud category only; not connected/enabled cloud service |
| `resource_python` | `settings.page.external_capabilities` | active pilot | Runtime category only |
| `resource_r` | `settings.page.external_capabilities` | active pilot | Runtime category only |
| `resource_go` | `settings.page.analysis_resources` | active pilot | Analysis resource category only |
| `resource_kegg` | `settings.page.analysis_resources` | active pilot | Analysis resource category only |
| `resource_analysis_package` | `settings.page.analysis_resources` | active pilot | Package category only |
| `resource_plotting_package` | `settings.page.analysis_resources` | active pilot | Plotting package category only |
| `resource_developer_diagnostics` | `settings.page.developer_diagnostics` | active pilot | Developer diagnostics category only |

## 5. Manifest Closure

| Manifest | Result |
| --- | --- |
| B8b5a production manifest | 13 rows, all `production_candidate=true`, all `replacement_ready=false`, no missing docs candidate paths |
| B8b5b active pilot manifest | 13 rows, all `active_pilot=true`, all `replacement_state=pilot_only`, all `replacement_ready=pilot_only`, no missing active paths |

Conclusion: B8b5a remains the docs-only production candidate source, and B8b5b records the narrow active pilot state. Neither manifest marks Settings resource icons as full final replacement.

## 6. Registry And Loader Closure

Implemented active registry / loader:

- `SETTINGS_RESOURCE_ICON_DIR`
- `SETTINGS_RESOURCE_ICON_PATHS`
- `load_settings_resource_icon`
- `load_settings_resource_pixmap`

Closure checks:

- registry has exactly 13 Settings resource keys
- registered active SVG paths exist
- unknown resource keys return empty icons
- non-P2 names such as status, export, empty-state, and App icon keys are not loaded through this loader
- paths are project-relative and derived from `PROJECT_ROOT`

## 7. Settings UI Wiring Closure

Active Settings surfaces using these icons:

- External capabilities
- Analysis resources
- Model and engine
- Developer diagnostics

UI marker:

- `QLabel#settingsResourceIcon`

Properties retained for testability:

- `resourceKey`
- `semanticKey`
- `moduleKey`
- `statusKey`
- `iconSource`
- `iconFallback`

Closure conclusion: icon wiring is limited to category markers inside existing Settings pages. It does not add pages, cards beyond the existing resource grouping, actions, cloud configuration, model execution, OCR execution, or resource detection logic.

## 8. Fallback Closure

Fallback behavior is covered and preserved:

- missing icons keep resource text labels visible
- status chips remain visible
- detect buttons remain enabled
- install / update buttons remain disabled
- cloud configuration buttons remain disabled
- Settings page navigation remains unchanged
- `iconFallback=true` records fallback state

The fallback test monkeypatches `load_settings_resource_pixmap` to return an empty pixmap and verifies the shell remains usable.

## 9. Settings Behavior Closure

| Behavior | Closure result |
| --- | --- |
| Settings secondary IA | Preserved |
| External capability detect-first UX | Preserved |
| Install/update action state | Still disabled |
| Cloud configuration action state | Still disabled |
| Status chips | Preserved |
| ImageJ/Fiji boundary | Remains Settings external capability; not LabTools first-level entry |
| Cloud AI boundary | Not shown as enabled cloud service |
| Local model boundary | Not shown as ready for direct inference |
| PDF/OCR boundary | Not shown as runnable OCR |
| Detection/install/update/cloud/model/OCR logic | Not implemented or changed |

## 10. Unprocessed Families

| Family | Closure state |
| --- | --- |
| `status` icons | Not processed in B8b5; still deferred for separate semantic review |
| `result_report_export` icons | Not processed in B8b5; still deferred for Result / Report / Export gating review |
| `empty_states` | Not processed in B8b5; still deferred |
| App icon / Finder icon / `.icns` / iconset / Info.plist / LaunchServices | Not processed; still deferred to UI-B10 |

Filesystem audit:

- `assets/icons/status/` does not exist
- `assets/icons/result_report_export/` does not exist
- `assets/icons/empty_states/` does not exist
- no App icon files were added or modified by B8b5b

## 11. Risk Register

| Risk | Mitigation | Residual status |
| --- | --- | --- |
| Settings resource icons imply installed/configured state | Icons are category markers only; no success/check treatment in manifest/report; status chips remain authoritative | Controlled |
| Cloud AI appears connected/enabled | Icon is used only in blocked Settings model-engine card; cloud config button remains disabled | Controlled |
| Local model appears inference-ready | Icon is used only in not-configured Settings model card | Controlled |
| PDF/OCR appears runnable | Icon is grouped with external capability category only; no OCR execution added | Controlled |
| ImageJ/Fiji becomes LabTools first-level entry | LabTools focused test verifies it remains absent from LabTools primary IA | Controlled |
| Production manifest becomes active-source manifest | B8b5a test preserves docs-only candidate paths while allowing B8b5b active pilot to remain scoped | Controlled |
| Status/result/export icons enter active assets prematurely | Focused tests and path audit block those families from Settings resource active directory | Controlled |

## 12. Test Coverage

| Test file | Coverage |
| --- | --- |
| `tests/ui/test_p2_settings_resource_icon_production_manifest.py` | B8b5a candidate manifest completeness, docs-only candidate paths, SVG/PNG validity, scoped active-pilot compatibility |
| `tests/ui/test_p2_settings_resource_icon_active_pilot.py` | active asset registration, loader fallback, Settings shell rendering, button gating, ImageJ/Fiji LabTools boundary, non-P2 exclusion |
| `tests/ui/test_settings_shell.py` | Settings secondary nav, detect-first controls, status chips, developer diagnostics |
| `tests/ui/test_labtools_shell.py` | LabTools primary IA boundary and ImageJ/Fiji exclusion |
| `tests/ui/test_module_selection.py`, `tests/ui/test_sidebar.py` | global shell regression |
| `tests/ui/test_app_identity.py` | app identity and icon asset inventory |
| `tests/ui/test_icon_resource_readiness_inventory.py` | readiness matrix guardrails |
| `tests/ui/test_p1_icon_production_manifest.py` | P1 production scope remains independent of P2 |

## 13. Closure Decision

P2 Settings resource icon sequence is closed as a narrow active pilot:

- UI-B8b5a production candidate stage: closed
- UI-B8b5b active pilot stage: closed

This closure does not mean Settings resource icon replacement is final. The current state is `pilot_only` and still depends on a future review before being treated as a full resource replacement baseline.

Recommended next decision:

- Do not proceed to status icons until a dedicated status semantic review is complete.
- Do not proceed to Result / Report / Export icons until a dedicated gating and affordance review is complete.
- Keep App icon / Finder icon / `.icns` / iconset / Info.plist / LaunchServices deferred to UI-B10.

## 14. Verification Commands

Commands run for this closure audit:

| Command | Result |
| --- | --- |
| `git status --short` | Clean before audit edits |
| `ls docs/ui \| rg 'B8b5[abc].*(report\|audit\|manifest\|pilot)\|B8b5a\|B8b5b'` | Found B8b5a/B8b5b reports and manifests |
| `find assets/icons/settings/resources -maxdepth 1 -type f \| sort \| wc -l` | Passed: 65 files |
| `rg -n "SETTINGS_RESOURCE_ICON\|load_settings_resource\|settingsResourceIcon\|resourceKeys\|B8b5" app tests docs/ui -g '*.py' -g '*.md' -g '*.csv'` | Passed: located registry, loader, wiring, tests, and reports |
| Python manifest/path audit script | Passed: 13 B8b5a rows, 13 B8b5b rows, no missing candidate or active paths |
| `sed -n '1,220p' docs/ui/UI_B8b5a_p2_settings_resource_icon_final_asset_production_report_20260521.md` | Read |
| `sed -n '1,220p' docs/ui/UI_B8b5b_p2_settings_resource_icon_replacement_pilot_20260521.md` | Read |

Additional validation:

| Command | Result |
| --- | --- |
| `python3 -m pytest -q tests/ui/test_p2_settings_resource_icon_production_manifest.py tests/ui/test_p2_settings_resource_icon_active_pilot.py` | Passed: 14 passed |
| `python3 -m pytest -q tests/ui/test_settings_shell.py tests/ui/test_labtools_shell.py tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/ui/test_app_identity.py` | Passed: 31 passed |
| `python3 -m app.main --smoke-test` | Passed |
| `git diff --check` | Passed |
| `git diff --cached --check` | Passed |

## 15. Non-Modification Statement

This closure audit adds only documentation. It does not modify:

- `app/**`
- `tests/**`
- `assets/**`
- `scripts/**`
- `dist/**`
- packaging files
- desktop entries
- App icon, Finder icon, `.icns`, iconset, Info.plist, or LaunchServices

No packaged app was built or run.
