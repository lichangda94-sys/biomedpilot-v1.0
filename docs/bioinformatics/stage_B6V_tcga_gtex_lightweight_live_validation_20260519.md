# Bioinformatics B6.V：TCGA / GTEx 轻量联网验收报告

生成日期：2026-05-19
当前基线 commit：`d2478ff Audit and close TCGA B6 upstream workflow`
验收性质：轻量联网测试与审计，不推进 B5.19，不实现 DEG/GSEA/KM/Cox/log-rank/report-ready。

## 1. 验收配置

- 验收项目根目录：`project_storage/bioinformatics/validation_runs/b6v_20260519_231732`
- 结果 JSON：`project_storage/bioinformatics/validation_runs/b6v_20260519_231732/b6v_light_live_validation_result.json`
- 限制开关：
  - `BIOINF_LIGHT_VALIDATION_MODE=1`
  - `BIOINF_TCGA_DOWNLOAD_LIMIT_FILES=2`
  - `BIOINF_GTEX_DOWNLOAD_LIMIT_FILES=1`
  - `BIOINF_GTEX_LIMIT_SAMPLES=3`
  - `BIOINF_GTEX_LIMIT_GENES=3`

## 2. TCGA 验收

- 测试 project：`TCGA-CHOL`
- 分析目的：`expression_clinical`
- 样本范围：`tumor` / `Primary Tumor`
- 是否真实联网：是，访问 GDC `/files`、`/cases` 与 `/data/{file_id}`。

### 2.1 Preview / Plan

- preview 状态：`ready`
- case 数：51
- sample 数：154
- file 数：35
- 预计总大小：148,124,181 bytes
- plan：`project_storage/bioinformatics/validation_runs/b6v_20260519_231732/acquisition/tcga_download_plans/tcga-plan-13a09d2c49.json`
- preview/plan 未写入 expression `source_files`，未生成 expression build manifest，未进入 DEG/GSEA ready。

### 2.2 Limited Download

- 下载限制：最多 2 个 GDC files。
- receipt：`project_storage/bioinformatics/validation_runs/b6v_20260519_231732/acquisition/download_receipts/tcga-dl-2284131136.json`
- 实际新下载：1
- cache hit：0
- 失败：1，原因为 GDC 连接被对端重置：`<urlopen error [Errno 54] Connection reset by peer>`
- 阻断：0
- 登记为可用 source file：1
- 实际下载大小：4,235,355 bytes
- 下载状态：`tcga_gdc_raw_files_acquired_with_warnings`
- 失败文件未进入 `source_files`；执行器继续处理其他文件。

### 2.3 Expression Build

- build manifest：`project_storage/bioinformatics/validation_runs/b6v_20260519_231732/standardized_data/tcga/tcga_chol/tcga_b64_ae0194ea18/data_prepared/tcga/tcga_expression_build_manifest.json`
- raw counts matrix：`project_storage/bioinformatics/validation_runs/b6v_20260519_231732/standardized_data/tcga/tcga_chol/tcga_b64_ae0194ea18/data_prepared/tcga/expression/tcga_expression_matrix.csv`
- sample metadata：`project_storage/bioinformatics/validation_runs/b6v_20260519_231732/standardized_data/tcga/tcga_chol/tcga_b64_ae0194ea18/data_prepared/tcga/sample_metadata/tcga_sample_metadata.csv`
- gene annotation：`project_storage/bioinformatics/validation_runs/b6v_20260519_231732/standardized_data/tcga/tcga_chol/tcga_b64_ae0194ea18/data_prepared/tcga/expression/tcga_gene_annotation.csv`
- sample/case/file mapping：`project_storage/bioinformatics/validation_runs/b6v_20260519_231732/standardized_data/tcga/tcga_chol/tcga_b64_ae0194ea18/data_prepared/tcga/sample_metadata/tcga_sample_file_mapping.csv`
- sample 数：1
- gene 数：60,660
- `validation_limited=true`
- 状态推进到 `pending_data_check`，但正式 DEG/GSEA/report-ready 被阻断。

### 2.4 Clinical Mapping

- clinical artifact manifest：`project_storage/bioinformatics/validation_runs/b6v_20260519_231732/acquisition/clinical_manifests/tcga-b66-d2765f6924.json`
- clinical receipt：`project_storage/bioinformatics/validation_runs/b6v_20260519_231732/acquisition/clinical_receipts/tcga-b66-d2765f6924.json`
- raw cases JSON：`project_storage/bioinformatics/validation_runs/b6v_20260519_231732/standardized_data/tcga/tcga_chol/tcga_b66_d2765f6924/clinical/tcga_clinical_raw_cases.json`
- case table：`project_storage/bioinformatics/validation_runs/b6v_20260519_231732/standardized_data/tcga/tcga_chol/tcga_b66_d2765f6924/clinical/tcga_clinical_case_table.tsv`
- diagnosis table：`project_storage/bioinformatics/validation_runs/b6v_20260519_231732/standardized_data/tcga/tcga_chol/tcga_b66_d2765f6924/clinical/tcga_clinical_diagnosis_table.tsv`
- follow-up table：`project_storage/bioinformatics/validation_runs/b6v_20260519_231732/standardized_data/tcga/tcga_chol/tcga_b66_d2765f6924/clinical/tcga_clinical_followup_table.tsv`
- survival table：`project_storage/bioinformatics/validation_runs/b6v_20260519_231732/standardized_data/tcga/tcga_chol/tcga_b66_d2765f6924/clinical/tcga_clinical_survival_table.tsv`
- mapping table：`project_storage/bioinformatics/validation_runs/b6v_20260519_231732/standardized_data/tcga/tcga_chol/tcga_b66_d2765f6924/clinical/tcga_clinical_mapping_table.tsv`
- case 数：1
- matched case 数：1
- matched sample 数：1
- basic OS 可用 case 数：1
- death event 数：1
- clinical status：`clinical_ready`
- survival status：`survival_ready_basic`，但只表示 preflight 输入可识别；未执行 KM/Cox/log-rank，未生成生存图或临床结论。

## 3. GTEx 验收

- 测试 tissue：`Minor Salivary Gland`
- 使用目的：`download_tissue_matrix`
- 是否真实联网：是，访问 GTEx Portal `/dataset/tissueSiteDetail`、`/expression/topExpressedGene`、`/expression/geneExpression`。

### 3.1 Preview / Plan

- preview 状态：`ready`
- sample 数：162
- donor 数：144
- file 数：1 个轻量 API slice 计划项
- plan：`project_storage/bioinformatics/validation_runs/b6v_20260519_231732/acquisition/gtex_download_plans/gtex-plan-e5e3ed1ad4.json`
- 页面/计划保留边界：GTEx 不自动作为 TCGA normal control，不自动与 TCGA 合并。

### 3.2 Limited Download / Build

- 下载策略：不下载完整 GTEx whole expression matrix；使用 GTEx API 生成 `3 genes x 3 samples` 的 validation slice。
- receipt：`project_storage/bioinformatics/validation_runs/b6v_20260519_231732/acquisition/download_receipts/gtex-dl-cf679c58fc.json`
- 实际下载/生成文件数：1
- 失败：0
- 文件大小：166 bytes
- raw slice：`project_storage/bioinformatics/validation_runs/b6v_20260519_231732/raw_data/gtex/gtex_minor_salivary_gland/gtex-dl-cf679c58fc/gtex_minor_salivary_gland_validation_expression_slice.tsv`
- build manifest：`project_storage/bioinformatics/validation_runs/b6v_20260519_231732/standardized_data/gtex/gtex_minor_salivary_gland/gtex-g63-b726587622/data_prepared/gtex/gtex_expression_build_manifest.json`
- expression matrix：`project_storage/bioinformatics/validation_runs/b6v_20260519_231732/standardized_data/gtex/gtex_minor_salivary_gland/gtex-g63-b726587622/data_prepared/gtex/expression/gtex_expression_matrix.csv`
- sample metadata：`project_storage/bioinformatics/validation_runs/b6v_20260519_231732/standardized_data/gtex/gtex_minor_salivary_gland/gtex-g63-b726587622/data_prepared/gtex/sample_metadata/gtex_sample_metadata.csv`
- gene 数：3
- sample 数：3
- `validation_limited=true`
- GTEx readiness 可识别 `gtex_expression_matrix`、`gtex_sample_metadata`、`gtex_donor_metadata`，但不会进入正式 DEG/GSEA/report-ready。

## 4. Scoped Workflow 回归

### TCGA project scoped lookup

- `TCGA-CHOL` 完成 preview/limited download/expression build/clinical build 后，切换到 `TCGA-UVM`。
- `TCGA-UVM` 在生成 plan 前：download、expression build、clinical、data check 全部未被 CHOL artifact 解锁。
- 为 `TCGA-UVM` 生成 preview/plan 后：UVM 仅解锁 download；expression build、clinical、data check 仍然 blocked。
- 切回 `TCGA-CHOL`：CHOL 仍保持 clinical completed / data check available。
- 结论：B6.8 的 project-scoped lookup 回归通过。

### GTEx tissue scoped lookup

- `Minor Salivary Gland` 完成 preview/download/build 后，切换到 `Fallopian Tube`。
- `Fallopian Tube` 在生成 plan 前：download、expression build、data check 全部未被 Salivary artifact 解锁。
- 为 `Fallopian Tube` 生成 preview/plan 后：只解锁 download；expression build/data check 仍然 blocked。
- 切回 `Minor Salivary Gland`：原 build 状态保持 completed。
- 结论：GTEx tissue-scoped workflow 回归通过。

## 5. 统一 Readiness 与边界

- readiness report：`project_storage/bioinformatics/validation_runs/b6v_20260519_231732/logs/readiness/readiness_report.json`
- capability matrix：`project_storage/bioinformatics/validation_runs/b6v_20260519_231732/manifests/analysis_capability_matrix.json`
- overall status：`ready_with_warnings`
- `validation_limited=true`
- 可识别输入：
  - TCGA：`tcga_expression_matrix`、`raw_count_matrix`、`tcga_sample_metadata`、`tcga_clinical_metadata`、`tcga_expression_clinical_mapping`
  - GTEx：`gtex_expression_matrix`、`gtex_sample_metadata`、`gtex_donor_metadata`
- 被阻断的正式分析行：`differential_expression`、`enrichment`、`gsea`、`correlation`、`survival`、`clinical_association`、`tcga_gtex_joint`、`reporting`
- 边界检查：
  - 未显示 TCGA+GTEx 自动合并 ready。
  - 未把 GTEx 自动作为 TCGA normal control。
  - 未自动运行 DEG/GSEA/KM/Cox/log-rank。
  - 未把轻量数据标记为 report-ready。

## 6. 发现的问题

### blocker

- 无。

### major

- 无。

### minor

- GTEx `/dataset/tissueSiteDetail` 在真实接口下会返回 tissue 列表；旧逻辑取第一条，可能把用户选择的 tissue 误显示为 Adipose - Subcutaneous。
- 当前 GTEx G6 默认没有安全的小体量下载/构建路径；直接做真实下载可能触发完整 GTEx 表达矩阵风险。
- GTEx API 与 GDC 在联网验收中都可能出现短暂 connection reset；需要下载事件保留失败并继续处理其他文件。

### note

- TCGA limited download 中 1/2 文件成功、1/2 文件因 GDC connection reset 失败；执行器正确保留失败事件且未登记失败文件。
- TCGA-CHOL 轻量 build 只有 1 个 tumor sample，不满足默认 tumor/normal 分组，readiness 正确提示只能展示/临床联合或手动分组。
- clinical basic OS 只有 1 个 death event，低于 warning 阈值；仅可进入 survival preflight，不可执行正式生存分析。

## 7. 已修复的问题

- 新增默认关闭的轻量联网验收模式与限制开关。
- TCGA 下载执行器支持 `BIOINF_TCGA_DOWNLOAD_LIMIT_FILES`，并将 `validation_limited=true` 写入 request/receipt/manifest/acquisition metadata。
- TCGA expression build 继承 `validation_limited`，readiness 对轻量数据阻断正式分析。
- GTEx preview 修复真实 API tissue 列表匹配，按用户选择的 tissue scoped 取 metadata。
- GTEx 增加 `gtex-api://expression-slice` 轻量 API slice 下载路径，默认仅在 `BIOINF_LIGHT_VALIDATION_MODE=1` 下生成。
- GTEx expression builder 支持 `BIOINF_GTEX_LIMIT_SAMPLES` / `BIOINF_GTEX_LIMIT_GENES`，并写入 `validation_limited=true`。
- GTEx workflow/UI 查找 plan/raw/build 时按当前 tissue scoped，不再被其他 tissue artifact 误解锁。
- readiness 增加 `validation_limited` 总标记和阻断提示，防止轻量验收数据进入正式 DEG/GSEA/KM/Cox/log-rank/report-ready。

## 8. 未修复但建议后续处理

- 如果需要更稳定的 GTEx sample-level 验收，可在后续增加官方 API 结果缓存或重试策略的用户可配置项。
- TCGA live download 对 GDC 单文件连接中断仍依赖用户重试；本阶段只验证失败事件和不中断其他文件的行为。
- B6.V 没有执行真实 UI 点击流；本次通过服务层、workflow state 和 UI 单元测试验证同一状态链路。

## 9. 验证命令与结果

- `BIOINF_LIGHT_VALIDATION_MODE=1 BIOINF_TCGA_DOWNLOAD_LIMIT_FILES=2 BIOINF_GTEX_DOWNLOAD_LIMIT_FILES=1 BIOINF_GTEX_LIMIT_SAMPLES=3 BIOINF_GTEX_LIMIT_GENES=3 python3 scripts/bioinformatics_light_live_validation.py`：通过，输出结果 JSON 如上。
- `python3 -m pytest tests/bioinformatics -q`：298 passed。
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`：171 passed。
- `python3 -m app.main --smoke-test`：通过，显示 `git_head=d2478ff`。
- `git diff --check`：通过。

## 10. 提交范围说明

- 本报告和轻量验收辅助代码可提交。
- 轻量验收数据目录 `project_storage/bioinformatics/validation_runs/` 仅作为本地验收产物，不纳入提交。
- 旧未跟踪文件 `docs/bioinformatics/Bioinformatics_handoff_report_20260513.md` 保持未跟踪原状，不纳入提交。
