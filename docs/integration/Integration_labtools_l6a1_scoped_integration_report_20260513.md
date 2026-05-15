# Integration LabTools L6A.1 Scoped Integration Report - 2026-05-13

## 1. Scope

This stage integrates LabTools L6A.1 into the Integration candidate source.

Integration rule for this stage:

- MainLine current stable baseline is the candidate source foundation.
- LabTools source is scoped to L6A.1 commit `63e7b5e` (`Harden LabTools ROI export packages`).
- LabTools current HEAD was read-only inspected at `0c1866e`, but later L6B/L6C files were intentionally excluded.
- No ReleaseBuild packaging was run.
- No desktop app was overwritten.
- No remote push was performed.
- No wholesale merge from LabTools was performed.

## 2. Baseline And Source

| Item | Value |
| --- | --- |
| Integration starting commit | `ed5855a` |
| MainLine baseline source | `stable/mainline` at `fd0b9a0` |
| LabTools scoped source | `dev/labtools` L6A.1 commit `63e7b5e` |
| LabTools current HEAD observed | `0c1866e` |
| Out-of-scope LabTools commits excluded | `bbaa221` recipe draft persistence; `0c1866e` experiment template drafts |

The Integration working tree was first refreshed to the MainLine `fd0b9a0` tree to satisfy the "MainLine current stable baseline" requirement. The previous Integration readiness report `docs/integration/Integration_package_readiness_audit_20260513.md` was preserved. LabTools was then applied by path from `63e7b5e`.

## 3. Scoped Apply File Set

LabTools module files applied from `63e7b5e`:

- `app/labtools/__init__.py`
- `app/labtools/workspace.py`
- `app/labtools/labtools_home.py`
- `app/labtools/calculators/__init__.py`
- `app/labtools/calculators/calculation_record.py`
- `app/labtools/calculators/calculator_models.py`
- `app/labtools/calculators/cell_seeding_calculator.py`
- `app/labtools/calculators/concentration_calculator.py`
- `app/labtools/calculators/dilution_calculator.py`
- `app/labtools/calculators/experiment_calculator_center.py`
- `app/labtools/calculators/qpcr_mix_calculator.py`
- `app/labtools/calculators/solution_preparation_calculator.py`
- `app/labtools/calculators/unit_conversion.py`
- `app/labtools/recipes/__init__.py`
- `app/labtools/recipes/built_in_recipes.py`
- `app/labtools/recipes/recipe_library.py`
- `app/labtools/recipes/recipe_models.py`
- `app/labtools/recipes/recipe_scaling.py`
- `app/labtools/recipes/recipe_source_draft.py`
- `app/labtools/recipes/recipe_source_importer.py`
- `app/labtools/recipes/recipe_source_models.py`
- `app/labtools/recipes/recipe_source_validation.py`
- `app/labtools/recipes/recipe_validation.py`
- `app/labtools/recipes/user_recipe_store.py`
- `app/labtools/image_analysis/__init__.py`
- `app/labtools/image_analysis/analysis_task.py`
- `app/labtools/image_analysis/audit_models.py`
- `app/labtools/image_analysis/export_package.py`
- `app/labtools/image_analysis/image_io.py`
- `app/labtools/image_analysis/image_models.py`
- `app/labtools/image_analysis/result_models.py`
- `app/labtools/image_analysis/roi_models.py`
- `app/labtools/image_analysis/fluorescence/__init__.py`
- `app/labtools/image_analysis/fluorescence/fluorescence_analyzer.py`
- `app/labtools/image_analysis/fluorescence/fluorescence_export.py`
- `app/labtools/image_analysis/fluorescence/fluorescence_models.py`
- `app/labtools/image_analysis/fluorescence/fluorescence_quality.py`
- `app/labtools/image_analysis/fluorescence/fluorescence_report.py`
- `app/labtools/image_analysis/wound_healing/__init__.py`
- `app/labtools/image_analysis/wound_healing/wound_analyzer.py`
- `app/labtools/image_analysis/wound_healing/wound_export.py`
- `app/labtools/image_analysis/wound_healing/wound_models.py`
- `app/labtools/image_analysis/wound_healing/wound_quality.py`
- `app/labtools/image_analysis/wound_healing/wound_report.py`
- `app/labtools/ui/__init__.py`
- `app/labtools/ui/calculator_widgets.py`
- `app/labtools/ui/image_analysis_widgets.py`
- `app/labtools/ui/recipe_widgets.py`

LabTools docs applied from `63e7b5e`:

- `docs/labtools_current_handoff.md`
- `docs/stage_labtools_l6a_image_roi_export_package_report.md`
- `docs/stage_labtools_l6a1_image_roi_export_hardening_report.md`

LabTools tests applied from `63e7b5e`:

- `tests/labtools/**`
- `tests/ui/test_labtools_image_export_ui.py`

Minimal MainLine shell/entry wiring changed in Integration:

- `app/main.py`
- `app/shell/dashboard.py`
- `app/shell/main_window.py`
- `app/shell/module_selection.py`
- `app/shell/sidebar.py`
- `tests/test_unified_entry.py`
- `tests/ui/test_module_selection.py`
- `tests/ui/test_sidebar.py`

MainLine baseline refresh also brought current MainLine files into Integration, including current Bioinformatics readiness gate, active Meta runtime baseline, shared UI helpers, UI governance docs, and MainLine handoff/cleanup docs. These were not sourced from LabTools and were required only to make Integration candidate source start from current MainLine.

## 4. Explicit Exclusions

Excluded LabTools current-HEAD files from later stages:

- `app/labtools/experiment_templates/**`
- `app/labtools/recipes/recipe_persistence.py`
- `app/labtools/ui/template_widgets.py`
- `docs/stage_labtools_l6b_recipe_draft_persistence_report.md`
- `docs/stage_labtools_l6c_experiment_templates_report.md`
- `tests/labtools/test_experiment_templates.py`
- `tests/labtools/test_recipe_persistence.py`

Excluded capabilities:

- New image algorithms.
- Automatic ROI.
- Automatic cell counting.
- Grayscale / ink-value / WB / gel grayscale analysis.
- Batch export.
- Autosave, database persistence, history system, or formal report system.
- OpenCV, scikit-image, ImageJ/Fiji, AI Gateway, local model calls, network access, or external downloads.

## 5. Integrated Capability

The integrated LabTools L6A.1 surface provides:

- Fluorescence manual ROI export package.
- Scratch/Wound manual ROI + threshold result export package.
- Manifest schema `labtools_roi_export_manifest.v1`.
- Stable CSV summary fields.
- Markdown auxiliary analysis fragment.
- ROI overlay PNG.
- Controlled `output_dir` validation and user-facing failure messages.
- No-overwrite file naming.
- Rollback of files created before a write failure.
- UI export helper feedback for cancel, failure, and success states.

## 6. Semantics Preserved

The integrated UI and services preserve these labels:

- LabTools is Developer Preview / testing.
- Fluorescence ROI is manual ROI grayscale measurement assistance.
- Scratch/Wound ROI is manual ROI + user threshold semi-quantitative area estimation.
- Export packages are auxiliary analysis materials requiring human review.
- Markdown fragment does not include the raw absolute source image path.
- Cell counting and densitometry / gray-value workflows remain `algorithm_not_available` or development placeholders.

## 7. Validation

Commands run in `/Users/changdali/Developer/biomedpilot v1.0/Integration`:

| Command | Result |
| --- | --- |
| `git diff --check` | passed |
| `python3 -m app.main --smoke-test` | passed; `workspace_entries=3`, `bioinformatics_features=5`, `meta_analysis_features=7`, `labtools_features=4` |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q` | passed; `130 passed in 1.50s` |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` | passed; `177 passed in 14.02s` |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/test_module_boundary_contract.py -q` | passed; `5 passed in 2.41s` |

Additional scope scan:

- No later `experiment_templates`, `recipe_persistence`, or `template_widgets` files are present in `app/labtools`.
- The only hits for OpenCV/scikit-image/ImageJ/Fiji/automatic ROI/cell counting/WB gray wording are prohibition text, guard tests, or disabled-source validation.

## 8. Decision

LabTools L6A.1 is integrated into the Integration candidate source as a scoped module surface.

This does not make LabTools production-ready, clinical-grade, submission-grade, or formal reporting capable. The module remains Developer Preview / testing with manual-review auxiliary output semantics.

## 9. Next Recommendation

Proceed to the next planned Integration step: Bioinformatics B5 scoped fix/integration.

Do not package `BioMedPilot Integration Preview.app` yet. ReleaseBuild packaging remains gated until Bioinformatics B5 scoped integration and final Integration validation pass.
