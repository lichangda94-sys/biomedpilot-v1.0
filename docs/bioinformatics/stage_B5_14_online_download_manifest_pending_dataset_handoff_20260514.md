# Bioinformatics B5.14 - Online Download Manifest and Pending Dataset Handoff

## 实现内容

- 将 B5.13 保存的 `acquisition/gse_file_download_candidates/<GSE>_download_candidates.json` 接入现有 GEO supplementary / Series Matrix 下载路径。
- `DatasetDownloadService.download_geo_manifest_assets()` 现在会在存在候选选择 manifest 时只下载用户选择的候选文件。
- 下载仍复用现有安全链路：
  - 写入 `acquisition/download_requests/<download_id>.json`
  - 下载到 `raw_data/geo/<GSE>/matrix` 或 `raw_data/geo/<GSE>/supplementary`
  - 更新 `<GSE>_asset_manifest.json`
  - 写入 `acquisition/download_receipts/<download_id>.json`
  - 调用 `register_acquisition()`
  - 将下载后的真实文件路径保存在 acquisition `source_files`
- 待处理数据集主表中，已下载的 GEO 候选资产按文件级显示；GEO 数据集选择列表仍保持数据集级显示。
- recognition 继续通过 acquisition record / handoff 中的 `source_files` 读取下载后的真实文件列表。

## Selection Manifest 语义

- 如果存在 B5.13 selection manifest：
  - 只下载 `selected=true` 的文件。
  - request / receipt 中记录 `download_candidate_selection_path`、`selected_candidate_ids`、`selected_file_names`。
  - 未选择的 remote assets 保留在 asset manifest 中，但不会阻塞当前选择批次的下载完成状态。
- 如果不存在 selection manifest：
  - 保持旧行为，下载 manifest 中待下载的 Series Matrix 和 supplementary files。

## Pending Dataset Handoff

- 下载完成后，`register_acquisition()` 使用 `strategy=reference` 绑定下载后的文件。
- acquisition record / handoff 中保留完整 `source_files`。
- 主待处理数据集表格会将多文件 GEO 下载批次展开为文件级行，便于用户看到每个 Series Matrix / supplementary 文件。
- 文件级行仍保留批次级完整 `source_files`，因此进入 recognition 时不会丢失同一下载批次中的其他文件。

## 未实现内容

- 未实现后台下载队列。
- 未实现取消下载。
- 未实现 RAW 预处理。
- 未实现真实 DEG executor。
- 未实现自动平台探针映射。
- 未自动确认样本分组、物种或表达值类型。
- 未修改 imported DEG report loop 语义。
- 未修改 Bioinformatics 以外模块。

## 测试结果

- `python3 -m pytest tests/bioinformatics -q`：245 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`：155 passed
- `python3 -m app.main --smoke-test`：passed
- `git diff --check`：passed
- `git diff --cached --check`：passed

## 已知边界

- 本阶段不提供大文件下载队列和取消能力，因此 RAW/heavy 文件仍应保持人工风险确认。
- 下载后的文件只进入 recognition / standardization confirmation 链路，不代表已经完成标准化或 DEG 分析。
- imported DEG candidate 仍只代表外部导入结果候选，不会写成软件计算结果。

## 下一步

B5.15 - Chinese topic search query draft carry-over，继续将旧版中文主题检索草稿能力按当前 Bioinformatics 架构做 scoped carry-over。
