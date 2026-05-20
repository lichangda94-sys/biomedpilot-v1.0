# Bioinformatics B5.13 - GSE File Discovery Download Candidate Carry-over

## 实现内容

- 新增 `app/bioinformatics/gse_file_download_candidates.py`，将当前 `GEO asset manifest` / `GeoMetadataProfileService` 中已发现的文件资产转换为可测试的下载候选选择 manifest。
- 在 GEO 数据集详情面板新增“可下载文件候选”区域，展示文件名、文件类型/预测角色、推荐级别、是否建议下载、风险提示、文件来源、后续用途和用户选择状态。
- 新增“保存候选选择”操作，将用户选择写入：
  - `acquisition/gse_file_download_candidates/<GSE>_download_candidates.json`
- 该 manifest 只保存候选选择，不执行真实批量下载，供 B5.14 做 online download manifest and pending dataset handoff。
- 保持本地多文件导入和 B5.10A 文件级待处理数据集表格逻辑不变。

## 未实现内容

- 未执行真实 GEO supplementary / Series Matrix 批量下载。
- 未实现真实 DEG executor。
- 未实现 RAW/CEL/FASTQ/SRA 预处理。
- 未实现平台探针到 gene symbol/gene ID 的自动映射。
- 未自动确认样本分组、物种或表达值类型。
- 未把 imported DEG candidate 写成软件计算结果。
- 未修改 Meta、LabTools、UIShell、Integration、ReleaseBuild、MainLine。

## 候选文件语义

- `series_matrix`：标记为 `expression_matrix_candidate`，适合后续进入 expression/metadata recognition，仍需 standardization confirmation。
- 高优先级 processed supplementary expression matrix：标记为 `expression_matrix_candidate`，可默认建议下载，仍需识别和标准化确认。
- sample/clinical/metadata supplementary：标记为 `sample_metadata_candidate`，可作为样本注释或候选分组来源，分组不能自动确认。
- platform/probe/annotation supplementary：标记为 `platform_annotation_candidate`，只表示平台注释候选，不承诺已完成 ID 映射。
- differential/DEG result supplementary：标记为 `imported_deg_candidate`，只作为外部导入结果候选，不作为 expression input，也不代表本软件计算。
- RAW/heavy 文件：标记为 `raw_heavy_risk_file`，用于提示风险，不进入默认选择。

## 默认选择规则

- 未下载的 Series Matrix 默认建议并选择。
- 未下载、低风险、高优先级的 processed supplementary expression matrix 默认建议并选择。
- family SOFT 已下载元数据容器不作为待下载候选默认选择。
- RAW/heavy 文件不默认选择。
- imported DEG candidate 不默认选择。
- platform annotation candidate 不默认选择，避免误导为已完成平台映射。

## 风险边界

- UI 明确提示“当前只是下载候选选择，不是分析结果”。
- 下载候选保存后仍必须经过 recognition 和 standardization confirmation。
- 主 UI 不显示 raw absolute path；内部 manifest 可保存 `remote_url` / `local_path` 供后续下载 handoff 使用。
- PubMed 不进入 Bioinformatics 数据获取主线，本阶段只处理 GSE/GEO asset manifest 候选。

## 测试结果

- `python3 -m pytest tests/bioinformatics -q`：244 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`：155 passed
- `python3 -m app.main --smoke-test`：passed
- `git diff --check`：passed
- `git diff --cached --check`：passed

## 下一步

B5.14 - Online download manifest and pending dataset handoff：读取本阶段保存的 candidate selection manifest，生成可执行的在线下载 manifest，将下载完成的文件按文件级 source_files handoff 加入待处理数据集，并继续进入 recognition / standardization confirmation。
