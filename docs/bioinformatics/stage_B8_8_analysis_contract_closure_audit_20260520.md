# B8.8 Analysis Contract Closure Audit

Date: 2026-05-20

Workspace: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

Branch: `dev/bioinformatics`

Audited baseline commit: `c2e3760 Add Bioinformatics B8 analysis contracts`

Audit outcome after B8.8 small fixes: 小问题通过

## 1. 审计范围

本次审计验收 `c2e3760` 是否符合 B8 / B8.0.1 的 analysis contract 边界。审计重点不是新增功能，而是确认新增 contract 是否避免把旧 runner、legacy、Integration 或 ReleaseBuild 逻辑误升级为正式分析功能。

Reviewed documents:

- `docs/bioinformatics/stage_B8_analysis_readiness_and_standardization_audit_20260520.md`
- `docs/bioinformatics/stage_B8_0_1_analysis_ui_prebuild_supplemental_audit_20260520.md`
- `docs/bioinformatics/stage_B8_1_standardized_analysis_input_resolver_20260520.md`
- `docs/bioinformatics/stage_B8_2_deg_ready_matrix_and_preflight_20260520.md`
- `docs/bioinformatics/stage_B8_3_controlled_deg_backend_mvp_20260520.md`
- `docs/bioinformatics/stage_B8_4_result_index_and_browser_foundation_20260520.md`
- `docs/bioinformatics/stage_B8_5_plot_artifact_schema_and_basic_plots_20260520.md`
- `docs/bioinformatics/stage_B8_6_report_ready_gate_and_export_package_20260520.md`
- `docs/bioinformatics/stage_B8_7_survival_and_clinical_association_design_20260520.md`

Reviewed runtime areas:

- `app/bioinformatics/analysis_inputs/*`
- `app/bioinformatics/analysis_task_runs.py`
- `app/bioinformatics/deg_ready/*`
- `app/bioinformatics/deg_engine/*`
- `app/bioinformatics/results/*`
- `app/bioinformatics/plots/*`
- `app/bioinformatics/reports/*`
- `app/bioinformatics/clinical_analysis/*`
- `app/bioinformatics/workflow_pages.py`
- related B8 tests under `tests/bioinformatics` and UI tests under `tests/ui`

## 2. B8.1-B8.7 验收表

| Stage | Scope | Result | Evidence | Notes |
| --- | --- | --- | --- | --- |
| B8.1 | Standardized resolver and task-run contract | 通过 | `analysis_inputs/resolver.py` reads repository/registry/input repository; `analysis_task_runs.py` exposes manifest-only contract | No formal execution added. UI now shows resolver package summary plus blocker/warning preview. |
| B8.2 | DEG-ready matrix and formal DEG preflight | 通过 | `deg_ready/builder.py` and `deg_ready/preflight.py` enforce sample alignment, gene mapping, value type policy | No p-value/FDR/table/plot result emitted. |
| B8.3 | Controlled DEG backend decision and MVP contract | 通过 | `deg_engine/dependency_check.py` detects numpy/pandas/scipy/statsmodels; `python_backend.py` blocks when dependencies/imports fail | No fallback p-value/FDR path. No runtime dependency added to `pyproject.toml`. |
| B8.4 | Result index foundation | 小问题通过 | `results/models.py`, `validation.py`, `migration.py`, `registry.py` enforce v2 fields and conservative migration | B8.8 fixed legacy semantics normalization for report gate compatibility. |
| B8.5 | Plot artifact schema and basic plot specs | 小问题通过 | `plots/models.py`, `schema.py`, `basic_renderers.py`, `registry.py` are spec/schema driven | B8.8 fixed legacy `preflight-only` normalization so preflight plots remain blocked. |
| B8.6 | Report-ready gate and export package | 小问题通过 | `reports/readiness.py` blocks missing provenance/deps/validation and non-formal results; `export_package.py` emits Markdown/artifact package only after gate | B8.8 fixed legacy `testing-level/imported result` semantics normalization. |
| B8.7 | Survival and clinical association design/preflight | 通过 | `clinical_analysis/*` only detects/preflights; forbidden outputs include KM/Cox/log-rank/HR/clinical advice | No KM/Cox/log-rank execution, HR, formal p-value, or KM plot. |

## 3. Resolver 输入来源检查

Status: 通过

`analysis_inputs/resolver.py` reads:

- `standardized_data/repositories/repository_manifest.json`
- `manifests/standardized_assets_registry.json`
- `standardized_data/repositories/analysis_input_repository/*.json`

It defines package types:

- `deg_recompute`
- `deg_imported_result`
- `enrichment_from_deg`
- `gsea_preranked`
- `correlation_expression`
- `immune_score_linkage`
- `tcga_clinical_survival_preflight`

Audit finding:

- No `load_recognition_report()` or `recognition_report.json` read exists in `analysis_inputs/*`.
- Existing `workflow_pages.py` and `reports/project_report_builder.py` still read recognition reports for UI/report draft context, not as formal analysis input.
- Multiple candidate matrices are blocked when no default is selected.
- GTEx is not auto-selected as TCGA normal control.

## 4. DEG-ready / DEG Backend 检查

Status: 通过

DEG-ready checks:

- GEO probe / ID_REF without mapping blocks via `geo_probe_or_id_ref_requires_platform_mapping` and `probe_or_id_ref_mapping_missing`.
- TPM/FPKM/log-normalized values do not enter count-model DEG.
- Unknown value type blocks formal DEG preflight.
- Sample/group mismatch, duplicate samples, empty group design, and no overlap block DEG-ready packages.

DEG backend checks:

- `check_deg_backend_dependencies()` is detect-first and records package availability/versions.
- `run_controlled_deg()` returns a blocked bundle when dependency snapshot is blocked.
- If a caller forges a passed snapshot but imports fail, backend still returns blocked and no p-values.
- No standard-library fallback p-values or FDR are emitted.
- No scipy/statsmodels/R/lifelines dependency was added.

## 5. Result Semantics 检查

Status: 小问题通过

Required semantics exist:

- `preflight_only`
- `testing_level`
- `exploratory`
- `formal_computed_result`
- `imported_external_result`
- `configured_not_run`
- `failed`
- `blocked`

Result index v2 required fields are defined and validated:

- `result_id`
- `task_run_id`
- `task_type`
- `result_semantics`
- `input_package_id`
- `source_dataset_id`
- `source_repository_manifest`
- `parameters_manifest`
- `engine_name`
- `engine_version`
- `dependency_snapshot`
- `output_artifacts`
- `plot_artifacts`
- `report_artifacts`
- `validation_status`
- `warnings`
- `blockers`
- `log_artifacts`
- `failure_reason`
- `created_at`
- `updated_at`
- `schema_version`
- `report_ready_eligible`
- `migration_status`

B8.8 small fix:

- Legacy display strings such as `testing-level`, `imported result`, and `preflight-only` are now normalized before report/plot gates make formal-readiness decisions.
- Migration still preserves legacy fields for existing imported DEG and UI compatibility, while exposing `canonical_result_semantics` for stricter gates.

## 6. Plot / Report / Survival 边界检查

Status: 小问题通过

Plot:

- Plot artifacts are spec/schema driven.
- No matplotlib/R plotting dependency is installed or required.
- Plot specs reference result index output artifacts, not runner temp CSV as authoritative formal input.
- Preflight-only sources are blocked; B8.8 extends this to legacy `preflight-only` labels.
- KM plot remains schema-only and blocked until a survival result schema exists.

Report:

- Existing report generation remains `draft_only`.
- Report-ready gate blocks missing result index, missing semantics, missing input package provenance, missing parameters, missing dependency snapshot, validation blockers, and non-formal testing/exploratory/imported/preflight results unless test report mode is explicit.
- Export package is Markdown/artifacts only; no PDF/DOCX dependency was added.
- No clinical advice is generated.

Survival / clinical:

- `clinical_analysis` only builds design/preflight artifacts.
- lifelines and R survival/survminer are detected as optional backends only.
- Outputs explicitly forbid KM plot, Cox hazard ratio, log-rank p-value, and clinical advice.
- Clinical association preflight reports variable types and missingness only; no formal p-value is computed.

## 7. UI 按钮和文案检查

Status: 小问题通过

Positive checks:

- Analysis Task Center shows resolver diagnostics.
- Formal DEG/GSEA/Survival/Plot/Report-ready are stated as still gate-disabled.
- Existing DEG page remains config/preflight only.
- Developer-only GEO DEG action still labels output as testing-level and not formal DEG.
- Imported DEG browser labels imported/external semantics.
- Immune/TME scoring remains exploratory and not deconvolution/clinical conclusion.
- Report page remains draft-only.

B8.8 small fix:

- Resolver summary now previews package blockers and warnings directly in the user-visible Analysis Task Center summary, not only in developer diagnostics JSON.

Remaining UI limitation:

- This is not yet the full Analysis UI rebuild. It is adequate for contract closure, but the next UI pass should add a dedicated package table with per-package blockers, warnings, disabled reasons, and repair actions.

## 8. Dependency Detection 检查

Status: 通过

DEG dependencies:

- numpy, pandas, scipy, statsmodels are detected via importlib/metadata.
- Missing dependencies produce blockers.
- No auto-install behavior exists.
- R backend is marked optional/not configured and is not called.

Survival dependencies:

- lifelines is detected via importlib/metadata.
- R survival/survminer are optional/not configured.
- Missing backend is reported as blocker, not traceback.

Packaging:

- No runtime dependency changes were made in `pyproject.toml`.
- Package smoke and LaunchServices smoke passed.

## 9. Legacy / Integration / ReleaseBuild 迁入边界检查

Status: 通过

No unchecked direct copy or formal upgrade was found.

Old implementation handling:

- GEO / TCGA old DEG runners remain outside formal B8 contract.
- Integration task-run/preflight ideas are not copied directly.
- ReleaseBuild/model9 analysis and report logic are documented as design references only.
- Existing developer GEO DEG runner still exists but is explicitly testing-level in UI/result semantics.
- Imported DEG remains external/imported and is not converted into recomputed BioMedPilot DEG.

## 10. 测试命令和结果

Required commands:

| Command | Result |
| --- | --- |
| `git diff --check` | Pass |
| `python3 -m pytest tests/bioinformatics -q` | Pass, `331 passed` |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` | Pass, `174 passed` |
| `python3 -m app.main --smoke-test` | Pass, source smoke |
| `python3 scripts/package_app.py --smoke-test` | Pass, packaged local Python launcher |
| `open -W -n dist/BioMedPilot.app --args --smoke-test` | Pass |
| `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app` | Pass |

Additional commands:

| Command | Result |
| --- | --- |
| `python3 -m pytest tests/bioinformatics -q -k "analysis_input or resolver or task_run"` | Pass, `12 passed, 319 deselected` |
| `python3 -m pytest tests/bioinformatics -q -k "deg_ready or deg_engine or dependency"` | Pass, `8 passed, 323 deselected` |
| `python3 -m pytest tests/bioinformatics -q -k "result_index or result_registry or result_semantics"` | Pass, `6 passed, 325 deselected` |
| `python3 -m pytest tests/bioinformatics -q -k "plot"` | Pass, `4 passed, 327 deselected` |
| `python3 -m pytest tests/bioinformatics -q -k "report"` | Pass, `25 passed, 306 deselected` |
| `python3 -m pytest tests/bioinformatics -q -k "survival or clinical"` | Pass, `27 passed, 304 deselected` |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q -k "bioinformatics"` | Pass, `120 passed, 54 deselected` |

Additional package checks:

- `CFBundleExecutable`: `BioMedPilot`
- Current Python architecture: `arm64`
- Codesign: valid on disk and satisfies designated requirement

## 11. Blocker / Major / Minor 问题

Blocker: none

Major: none

Minor fixed in B8.8:

1. Report-ready gate now normalizes legacy result semantics before non-formal blocking.
2. Plot schema and plot spec generation now normalize legacy `preflight-only` before plot eligibility checks.
3. Analysis Task Center resolver summary now displays blocker/warning previews directly.

Minor remaining:

1. Analysis UI still needs a richer package table and repair-action UX. This belongs to Analysis UI rebuild, not B8 contract closure.
2. Settings does not yet expose a dedicated analysis dependency panel. The detect-first contracts exist in backend modules, but UI surfacing belongs to the next UI/settings pass.

## 12. 最终结论

Final conclusion: 小问题通过

`c2e3760` established the intended B8 analysis contracts and did not introduce formal GSEA, formal survival analysis, formal plotting, or report-ready large features. B8.8 found no blocker or major issue. The small compatibility and UI-diagnostics issues found during audit were fixed and covered by tests.

## 13. 是否建议进入 Analysis UI rebuild

建议进入 Analysis UI rebuild。

Rationale:

- Resolver, DEG-ready, result index, plot schema, report gate, and survival/clinical preflight contracts now exist.
- The UI can now be rebuilt around package tables, blocker/warning repair actions, disabled reasons, dependency status, result semantics, and report-ready gate state without inventing new backend semantics.

Scope warning:

- Rebuild should still avoid enabling formal DEG/GSEA/survival/plot/report-ready buttons until each gate passes.

## 14. 是否建议进入 B9.1 Formal DEG Dependency Activation

建议有条件进入 B9.1 dependency activation planning, but not automatic formal DEG enablement.

Allowed next step:

- Audit and decide whether to add scipy/statsmodels as runtime/package dependencies.
- Add Settings dependency status UI.
- Add packaging impact checks.
- Only then enable a formal DEG path when resolver package, DEG-ready preflight, dependency snapshot, parameters, result schema, and result index registration all pass.

Do not do next:

- Do not silently install dependencies.
- Do not call R/DESeq2/edgeR/limma.
- Do not expose formal DEG from legacy GEO/TCGA runners.
