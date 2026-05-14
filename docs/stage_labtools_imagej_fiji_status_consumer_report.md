# LabTools ImageJ/Fiji Status Consumer Report

Date: 2026-05-14

## Stage name

LabTools ImageJ/Fiji status consumer.

## Worktree

- Worktree: `/Users/changdali/Developer/biomedpilot v1.0/LabTools`
- Branch: `dev/labtools`
- Starting commit: `1221311 docs(labtools): align local tools model ux`
- Ending commit: this report's containing commit; see `git log --oneline -5` after commit.

## Scope

LabTools is now a consumer of the shared ImageJ/Fiji local-engine layer from Integration commit `5cda2bc`.

In scope:

- Carry over `app/shared/local_engines`.
- Replace LabTools-owned ImageJ/Fiji detection/config logic with a thin LabTools status consumer.
- Show lightweight ImageJ/Fiji status only in image-related LabTools entry points.
- Preserve existing manual ROI MVP workflows and ROI export behavior.
- Update tests and documentation.

## Files changed

- `app/shared/local_engines/__init__.py`
- `app/shared/local_engines/engine_config.py`
- `app/shared/local_engines/engine_status.py`
- `app/shared/local_engines/imagej_fiji_bridge.py`
- `app/shared/local_engines/imagej_fiji_detector.py`
- `app/shared/local_engines/install_guides.py`
- `app/labtools/imagej_bridge.py`
- `app/labtools/ui/imagej_bridge_widgets.py`
- `app/labtools/ui/image_analysis_widgets.py`
- `app/labtools/ui/western_blot_widgets.py`
- `app/labtools/workspace.py`
- `tests/shared/test_local_engines_imagej_fiji.py`
- `tests/labtools/test_imagej_bridge.py`
- `tests/labtools/test_labtools_imports.py`
- `tests/ui/test_labtools_imagej_bridge_ui.py`
- `tests/ui/test_labtools_module_architecture.py`
- `tests/ui/test_module_selection.py`
- `docs/labtools_current_handoff.md`
- `docs/labtools_schema_index.md`
- `docs/labtools_tool_logic_audit.md`
- `docs/stage_labtools_imagej_fiji_status_consumer_report.md`

## Shared local_engines reuse

The shared layer was carried over from Integration commit `5cda2bc`.

LabTools no longer owns a separate full ImageJ/Fiji detection/config framework. `app/labtools/imagej_bridge.py` is now a thin consumer boundary that reads `EngineStatus` through `ImageJFijiBridge` and maps it to LabTools UI wording.

## UI behavior

ImageJ/Fiji status is now feature-triggered:

- Western Blot -> 结果与灰度分析 shows a contextual ImageJ/Fiji status panel.
- LabTools 图像定量 shows a contextual ImageJ/Fiji status panel.
- Missing ImageJ/Fiji shows a setup prompt explaining that the workflow needs local ImageJ/Fiji, BioMedPilot does not silently download or install it, and the user can auto-detect, choose a path, read the install guide, or continue available manual/testing MVP workflows when applicable.
- Available ImageJ/Fiji shows available status and version information if present.
- Failed validation shows a safe Chinese error summary.
- Non-image LabTools features are not blocked and do not show ImageJ/Fiji prompts.

The prominent LabTools header-level ImageJ/Fiji configuration page was removed. If a future shared `设置 > 本地工具与模型` page exists, LabTools can add a navigation hook to that shared page instead of creating a LabTools-only settings center.

## Manual ROI preservation

Existing fluorescence manual ROI and wound / scratch manual ROI + threshold tools remain accessible as local manual/testing MVP workflows. Their outputs remain manual-review auxiliary results. ROI export behavior is unchanged.

## Explicit non-goals

- No WB/gel grayscale analysis.
- No agarose gel analysis.
- No cell counting.
- No pathology analysis.
- No automatic ROI.
- No new image algorithms.
- No cloud AI, account, payment, credits, server upload, packaging, local LLM, or Ollama changes.
- No OpenCV, scikit-image, PyImageJ, or Fiji/ImageJ bundling.

## Validation results

- `python3 -m pytest tests/shared/test_local_engines_imagej_fiji.py tests/labtools/test_imagej_bridge.py -q`: 14 passed
- `python3 -m pytest tests/labtools -q`: 196 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`: 198 passed
- `python3 -m app.main --smoke-test`: passed; output included `git_head=1221311`, `workspace_entries=3`, `labtools_features=6`
- `python3 -m compileall app/labtools`: passed
- `git diff --check`: passed
- `git diff --cached --check`: passed before commit

## Known limitations

- No shared global settings page is wired in this worktree, so LabTools uses contextual setup panels only.
- The shared status layer confirms ImageJ/Fiji availability; it does not make any concrete LabTools image workflow available.
- Concrete ImageJ/Fiji-backed workflows still require a separate Tool Logic Card before implementation.

## Next recommended stage

Create a Tool Logic Card for the first ImageJ/Fiji-backed macro workflow, likely WB/gel grayscale or wound workflow redesign. The card should define input image constraints, macro parameters, macro provenance, output files, result fields, warnings, review wording, export policy, and fallback/manual-review behavior.

## Git status

Pending final commit.
