# Bioinformatics B5.15 - Integration Handoff Audit

日期：2026-05-14

范围：审计并固化 B5.13/B5.14 后续的 acquisition、recognition v2、standardization repository 三段实现，准备交给 Integration 进行下一步合并和 Preview 定界。本报告只记录当前 `dev/bioinformatics` runtime 状态，不迁移 Integration 文件，不运行桌面打包。

## 0. 当前分支与提交

- 工作区：`/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`
- 分支：`dev/bioinformatics`
- 当前 HEAD：`1cbfc79 feat(bio): add standardization repositories`

本轮相关提交：

- `8beedae feat(bio): complete acquisition file manifest handoff`
- `84a6677 feat(bio): upgrade recognition report schema`
- `1cbfc79 feat(bio): add standardization repositories`

保留未跟踪文件，未纳入本阶段提交：

- `docs/bioinformatics/.stage_B5_12_legacy_acquisition_standardization_audit_20260514.md.swp`
- `docs/bioinformatics/Bioinformatics_handoff_report_20260513.md`

## 1. 已完成能力审计

### Acquisition

已完成：

- 所有下载/本地导入落地文件通过统一 file record 记录 `source`、`source_url/source_path`、`local_path`、`status`、`size_bytes`、`sha256`、`role`、`risk_level`。
- GEO selected assets 下载会写 request、receipt、asset manifest、source manifest，并通过 `register_acquisition()` 写入 acquisition record。
- 缓存命中、失败、跳过、RAW/heavy 阻断都进入 receipt / manifest。
- 本地 copy/reference 导入统一生成 source manifest，并继续用 acquisition `source_files` 进入 pending dataset 和 recognition。
- TCGA/GDC、GTEx 的服务层边界已定为真实 open/public 下载或 prepared package import，不创建假文件。

当前边界：

- 无后台下载队列、取消、正式 retry UI。
- RAW/heavy 普通流程默认阻断，无 override。
- TCGA/GDC、GTEx 在线下载能力仍需要 Integration 后继续扩展 UI 与 live API 验证。

### Recognition

已完成：

- `recognition_report.json` 升级为 `biomedpilot.recognition_report.v2`。
- `recognized_files.json` 升级为 `biomedpilot.recognized_files.v2`。
- 每次识别写入 `recognition_run_id`、`recognition_engine_version`、输入 fingerprint、stale status。
- 文件级输出新增 `primary_type`、`roles`、`standardization_status`、`evidence`、`matrix_profile`、`metadata_profile`、`risk_profile`。
- RAW/heavy 优先阻断；GEO Series Matrix / family.soft 优先解析；TCGA、GTEx、GDC manifest 在 generic profile 基础上做专用分类。
- imported DEG 与 expression matrix 更严格区分，DEG 结果不进入 recompute DEG 输入。
- UI 显示 `可进入标准化`、`仅作参考/注释`、`不能用于分析`。

当前边界：

- recognition 输出仍是候选和 evidence，不代表标准化完成。
- Series Matrix / SOFT 可解析结构与预览，但不自动完成平台映射或分组确认。
- stale report 会提示重新识别，不能作为无声下游输入。

### Standardization Repository

已完成：

- `project_standardization.py` 从轻量 registry 升级为 repository 分流器。
- 新增 repository 根目录：`standardized_data/repositories/`。
- 输出仓库：
  - `expression_repository`
  - `sample_metadata_repository`
  - `group_design_repository`
  - `feature_annotation_repository`
  - `clinical_repository`
  - `imported_result_repository`
  - `analysis_input_repository`
- 写入：
  - `standardized_data/repositories/repository_manifest.json`
  - `standardized_data/repositories/validation_report.json`
  - `standardized_data/repositories/asset_lineage.jsonl`
  - `manifests/standardized_assets_registry.json` v2
  - `standardized_data/analysis_ready_assets/analysis_ready_manifest.json` v2
- 表达矩阵只整理为内部标准方向和标准字段，记录 `biological_normalization_performed=false`。
- imported DEG 单独进入 `imported_result_repository`，可作为浏览/富集输入，不作为软件重新计算 DEG 的表达输入。
- `analysis_input_repository` 生成明确 input package：
  - `deg_recompute`
  - `enrichment_from_imported_result`
  - `correlation_heatmap`
  - `survival`
- DEG preflight 优先从 `analysis_input_repository` 读取 package，旧 registry 读取保持兼容。
- 多候选默认资产有 selection state；单候选自动推荐但记录状态，多候选未确认时阻断稳定分析输入。

当前边界：

- 不运行 limma / DESeq2 / edgeR。
- 不做 biological normalization。
- probe/ID_REF 缺平台注释时可登记 expression repository，但 recompute DEG package 被阻断。
- sample alignment 现在用于 validation/package gate，不等于最终统计设计校验完成。

## 2. 当前真实链路

当前可描述为：

`acquisition record + source manifest + receipt + real source_files`
→ `pending dataset`
→ `recognition_report.v2 / recognized_files.v2`
→ `standardization_confirmation.json`
→ `standardized_data/repositories/*`
→ `analysis_input_repository/*`
→ `DEG preflight / enrichment / correlation / survival 的输入包`

这条链路可以证明“数据真实进入项目，并被整理为 BioMedPilot 内部标准资产”。不能证明“已经完成正式分析”。

## 3. Integration Carry-over 建议

Integration 合并时优先 carry-over：

1. `app/bioinformatics/acquisition_file_records.py`
2. `app/bioinformatics/project_workspace_binding.py` 中 source manifest / file record metadata 扩展
3. `app/bioinformatics/download/dataset_download_service.py` 中 GEO selected assets 下载、receipt、RAW/heavy 阻断、cache hit 记录
4. `app/bioinformatics/project_recognition.py` recognition v2 schema、stale 检测、TCGA/GTEx/GDC/RAW-heavy 分类
5. `app/bioinformatics/project_standardization.py` repository 分流器和 manifest v2
6. `app/bioinformatics/standardization_confirmation.py` 候选 lineage 字段
7. `app/bioinformatics/deg_task_plan.py` analysis input package 优先读取
8. `app/bioinformatics/workflow_pages.py` acquisition / recognition / standardization 页面展示边界
9. 对应测试：
   - `tests/bioinformatics/test_dataset_download_service.py`
   - `tests/bioinformatics/test_workflow_adapters.py`
   - `tests/ui/test_bioinformatics_workflow_pages.py`

Integration 合并时需要人工比较的文件：

- `app/bioinformatics/standardized_asset_selection.py`
  - Integration 曾有默认资产选择思路；当前分支已在 registry v2 中写 selection state。
  - 建议保留当前 repository manifest 为 truth，再决定是否把 Integration resolver 接到 repository manifest。
- `app/bioinformatics/recognition_detail_report.py`
- `app/bioinformatics/recognition_next_steps.py`
  - 若 Integration 仍需要这些 UI/helper，建议改为读取 recognition v2 字段，而不是继续读旧 v1 表面字段。
- `app/bioinformatics/deg_executor_preflight.py`
  - 若保留，应改为读取 `analysis_input_repository` package，而不是直接扫描 recognition。
- `app/bioinformatics/analysis_task_runs.py`
  - 若进入 Preview，应明确任务运行记录和真实 executor 的边界。

## 4. Preview / Integration 边界

可以进入 Integration Preview 的承诺：

- 本地导入、GEO 下载、本地引用都能生成 source manifest / receipt / acquisition record。
- 只有真实存在的文件进入 pending dataset 和 recognition。
- recognition 能把 GEO / TCGA / GTEx / local processed / metadata / clinical / annotation / imported DEG / RAW-heavy 分为可标准化、参考、阻断。
- standardization 能生成内部 repository 和 analysis input package。
- imported DEG 不会被误当作 recompute DEG 输入。
- probe mapping 缺失、unknown value type、sample mismatch、非数值表达值、negative count、重复 gene ID 会进入 validation report 或 package blocker。

不应进入 Integration Preview 的承诺：

- 不承诺 RAW preprocessing。
- 不承诺 controlled access TCGA。
- 不承诺 GTEx/TCGA 联合分析正式可用。
- 不承诺 biological normalization。
- 不承诺自动平台探针映射。
- 不承诺正式 DEG executor 已可发表使用。
- 不承诺所有外部下载 API 已完成 live network 验证。

## 5. 下一步建议

P0 - Integration merge：

- 以 `1cbfc79` 为 Bioinformatics 当前交接点。
- 先做文件级 merge audit，避免 Integration 旧 helper 覆盖当前 v2 schema。
- 合并后立即跑 `tests/bioinformatics` 与 `tests/ui/test_bioinformatics_workflow_pages.py`。

P1 - Resolver 收口：

- 新增或改造 asset resolver，只读取 `standardized_data/repositories/repository_manifest.json` 和 `analysis_input_repository`。
- 下游模块停止直接扫描 recognition report 或旧 analysis-ready manifest。

P2 - TCGA / GTEx 下载 UI：

- 补 GDC file selection UI、open access 限制、大文件阻断提示。
- 补 GTEx tissue/reference package selection。
- 下载后必须走 acquisition record → pending dataset → recognition v2。

P3 - Platform mapping：

- 按 `feature_annotation_repository` 增加 mapping quality preview。
- 不自动宣称 mapping 成功；只在用户确认平台注释后解除 probe mapping blocker。

P4 - Preview packaging：

- 若进入 packaged Integration Preview，不能只跑 `python3 -m app.main --smoke-test`。
- 需要增加 LaunchServices / Finder-style `.app` gate：`open -W -n`、`-psn_*` 参数处理、`CFBundleExecutable`、codesign、Apple Silicon `arm64` 进程检查。

## 6. 已执行验证

最近一次验证命令：

- `python3 -m pytest tests/bioinformatics -q`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q`
- `python3 -m app.main --smoke-test`
- `git diff --check`

验证结果：

- `tests/bioinformatics`：251 passed
- `tests/ui/test_bioinformatics_workflow_pages.py`：91 passed
- source smoke：passed
- diff check：passed

## 7. Integration 接手检查表

- 确认当前 source branch 为 `dev/bioinformatics`，handoff HEAD 为 `1cbfc79` 或包含该提交。
- 合并前保护 recognition v2 / repository v2 schema。
- 合并后检查 `standardized_data/repositories/` 是否仍由 `project_standardization.py` 生成。
- 合并后检查 imported DEG 不进入 recompute DEG package。
- 合并后检查 RAW/heavy 即使被手动选中也被服务层阻断。
- 合并后检查 stale recognition / stale repository 都会提示重跑。
- 合并后如要发布 `.app`，执行 LaunchServices packaging gate。
