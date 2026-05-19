# Bioinformatics B6.3 TCGA Real Download Executor

## 阶段目标

B6.3 将 B6.2 的 TCGA metadata preview / download plan draft 推进到真实 GDC 文件下载执行。执行器读取 `acquisition/tcga_download_plans/*.json`，下载开放 GDC files，记录缓存命中、失败、阻断和 receipt/source manifest/acquisition record。

本阶段只覆盖 TCGA/GDC，不触碰 GTEx，不推进 B5.19，不构建最终表达矩阵，不进入 DEG/GSEA ready。

## 实现内容

- B6.2 plan writer 现在持久化完整 `file_manifest_entries`，包含 GDC file id、文件名、大小、访问类型、data type、data format、workflow 和 sample types。
- 新增 TCGA download plan executor：
  - 读取 B6.2 `draft_only` plan。
  - 对旧 plan 缺失 `file_manifest_entries` 的情况，通过 plan 中的 GDC filters 重新查询 `/files`。
  - 只允许 open 且非 RAW/alignment/controlled 的 GDC file 下载。
  - 单文件失败不会中断后续文件。
  - 已存在文件由底层 GDC downloader 计为 cache hit。
- 下载执行写入：
  - `acquisition/download_requests/*.json`
  - `acquisition/download_receipts/*.json`
  - `raw_data/tcga/<project_id>/<download_id>/*`
  - `raw_data/tcga/<project_id>/<download_id>/<project_id>_gdc_download_manifest.json`
  - acquisition record / source manifest / handoff
- TCGA 页面新增 `下载 TCGA 原始文件`，显示成功、缓存、失败、阻断、总大小、本地缓存路径和 receipt 路径。

## 阶段边界

- 下载成功文件会注册为 acquisition `source_files`。
- 即使存在 `source_files`，TCGA B6.3 记录仍设置：
  - `ready_for_recognition = pending_expression_matrix_build`
  - `analysis_gate_status = waiting_b6_4_expression_matrix_build`
  - `recognition_scope = tcga_raw_files_waiting_b6_4`
- 数据源列表显示“TCGA 原始文件已获取，等待 B6.4 构建表达矩阵”。
- ready count 仍为 0，不进入 DEG/GSEA ready。
- GTEx 仍保持 B6.2 边界，不接入本阶段下载执行。

## 测试结果

- 定向测试：
  - `python3 -m pytest tests/bioinformatics/test_tcga_download_executor.py tests/bioinformatics/test_dataset_download_service.py tests/bioinformatics/test_data_source_registries.py -q`
  - `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k 'data_source_tcga or chinese_dataset_search_registers_candidate'`
- 完整回归结果以本次提交完成汇报为准。

## 保留未动

- `docs/bioinformatics/Bioinformatics_handoff_report_20260513.md` 仍为旧未跟踪文件，本阶段不纳入提交。
