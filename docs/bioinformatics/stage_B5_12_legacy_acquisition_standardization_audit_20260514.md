# Stage B5.12 - Legacy Acquisition-to-Standardization Capability Audit

Date: 2026-05-14

Scope: read-only capability audit. Runtime code was not changed. No network download was executed.

## 搜索范围

当前 Bioinformatics worktree:

- `app/bioinformatics/**`
- `tests/bioinformatics/**`
- `docs/bioinformatics/**`

只读对比源码:

- `/Users/changdali/Developer/biomedpilot v1.0/MainLine`
- `/Users/changdali/Developer/biomedpilot v1.0/Integration`
- `/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild`

明确旧版源码:

- `app/bioinformatics/legacy/**`
- `ReleaseBuild/archive/legacy_sources/model9/**`
- MainLine / ReleaseBuild 中的 `archive/legacy_sources/bioinformatics_project/**`

未使用桌面 `.app` bundle 作为证据，未反编译，未修改 `dist` 或桌面入口。

## 已找到的旧功能文件清单

当前 runtime / current workflow:

- `app/bioinformatics/workflow_pages.py`
  - 数据导入页、GSE 编号入口、中文研究主题入口、待处理数据集表、GEO asset manifest 下载按钮、标准化确认 UI。
- `app/bioinformatics/project_workspace_binding.py`
  - `register_acquisition()` 生成 acquisition plan / record / handoff，保留 `source_files`、`copied_files`、`referenced_paths`。
- `app/bioinformatics/download/dataset_download_service.py`
  - `DatasetDownloadService`、`HttpsGeoFamilySoftDownloader`、`HttpsGeoAssetManifestDiscoverer`、`download_geo_manifest_assets()`。
- `app/bioinformatics/services/geo_metadata_profile_service.py`
  - family SOFT / Series Matrix metadata profile、supplementary 文件预测、RAW 风险标记、候选下载建议。
- `app/bioinformatics/search_center/**`
  - GEO / TCGA GDC / GTEx 三源 router、query understanding、normalizer、ranker。
- `app/bioinformatics/retrieval/bio_query_adapter.py`
  - 中文问题转生信数据检索草稿，显式移除 PubMed query candidates。
- `app/bioinformatics/project_recognition.py`
  - Series Matrix、family.soft、XLSX、CSV/TSV、metadata、annotation、imported DEG 识别。
- `app/bioinformatics/geo_series_matrix_parser.py`
  - 当前 Series Matrix MVP parser。
- `app/bioinformatics/geo_family_soft_parser.py`
  - 当前 family.soft parser。
- `app/bioinformatics/standardization_confirmation.py`
  - recognition candidates -> confirmation candidates -> `standardization_confirmation.json`。
- `app/bioinformatics/project_standardization.py`
  - `standardized_assets_registry.json`、`analysis_ready_manifest.json`、`data_processing_task_plan.json` 的轻量资产注册。

当前 / legacy lineage:

- `app/bioinformatics/legacy/geo_processing/download_validator.py`
  - 文件级扫描、打分、RAW / Series Matrix / family.soft / supplementary / annotation / expression candidate 分类、module1 handoff 输出。
- `app/bioinformatics/legacy/geo_processing/module1_readers.py`
  - legacy search result / download plan / receipt / file inventory / parser hints / dataset manifest draft / module1 handoff 读取与规范化。
- `app/bioinformatics/legacy/geo_processing/module3_assets.py`
  - legacy Module3 标准资产 layout：expression_gene、sample_annotation、feature_annotation、dataset_manifest。
- `app/bioinformatics/legacy/geo_tool/geo_pipeline/download.py`
  - GEOparse family SOFT 下载、Series Matrix / supplementary 候选发现和 execution 逻辑。
- `app/bioinformatics/legacy/geo_tool/geo_pipeline/process.py`
  - family SOFT GEOparse processing、phenotype、GPL annotation、expression matrix、gene-level aggregation。
- `app/bioinformatics/legacy/tcga_gtex/**`
  - TCGA/GTEx legacy query / mock download manifest / runtime facade。

ReleaseBuild archive `model9`:

- `geo_readiness/series_matrix_parser.py`
  - Series Matrix metadata 和 expression table parser。
- `geo_readiness/soft_parser.py`
  - SOFT metadata、sample table expression parser。
- `geo_readiness/platform_annotation_parser.py`
  - probe-to-gene-symbol mapping quality report。
- `local_data/standardizer.py`
  - 用户选择 expression matrix / metadata / gene annotation 后复制到 standardized local dataset，并生成 validation report。

MainLine / Integration / ReleaseBuild 对比:

- 三个 sibling worktree 均包含与当前相近的 Bioinformatics runtime surface 和 legacy GEO source。
- MainLine HEAD: `56dba09 docs: align local tools model architecture`
- Integration HEAD: `6fae058 docs(integration): align local tools model architecture`
- ReleaseBuild HEAD: `b6fb829 docs(release): align local tools model architecture`
- 对比树中可见 `BioinformaticsSourceRouter`、`HttpsGeoAssetManifestDiscoverer`、`download_geo_manifest_assets()`、`project_standardization.py`、legacy `module1_handoff` lineage。

## 联网检索能力结论

当前 runtime 已有三类生信数据检索入口:

- GSE 编号检索：`workflow_pages.py` 通过 GEO candidate detail / acquisition record 加入项目。
- GEO 数据集检索：`search_center.geo_adapter.GeoSearchAdapter` 调用 `search_geo_datasets_for_queries()`，支持 limit / pagination / fetcher injection。
- 中文研究主题检索：`BioinformaticsSourceRouter` 先运行 `QueryUnderstandingLayer`，生成 GEO / TCGA / GTEx 分源候选。

TCGA / GTEx:

- `search_center.tcga_gdc_adapter` 可查询 GDC project、file inventory、cases。
- `search_center.gtex_adapter` 可查询 GTEx tissue expression reference，并提示 GTEx 为 normal reference 和 batch risk。
- `DatasetDownloadService` 对 TCGA / GTEx 当前只生成 download manifest，不伪造已下载表达矩阵。

Query draft / 医学词库 / 本地模型:

- `retrieval/bio_query_adapter.py` 和 `search_center/query_understanding.py` 支持中文问题到英文 GEO query、TCGA project、GTEx tissue 的草稿。
- Router 支持 `use_local_model` / `LocalModelConfig` / gateway task type，但默认可 offline draft。
- 当前 tests 覆盖“只允许 geo / tcga_gdc / gtex，不能混入 PubMed”。

PubMed 边界:

- 当前 Bioinformatics search center 不以 PubMed 作为数据检索源。
- `bio_query_adapter` 审计字段包含 `pubmed_query_candidates_removed`。
- legacy `app/bioinformatics/legacy/literature_cli.py` 是旧 PubMed 文献 CLI，不属于当前 Bioinformatics 数据获取主线。
- GEO metadata 可显示 PMID / `Series_pubmed_id`，这只是数据集 metadata 字段，不等于 Bioinformatics 执行 PubMed 检索。

结论：联网检索主能力已经在当前 runtime 中存在，但要进入 Integration Preview，应保持用户确认、限流、错误提示和“不检索 PubMed”的边界。

## GEO 文件发现 / 下载候选能力结论

当前 runtime 已有 GEO 文件发现能力:

- `HttpsGeoAssetManifestDiscoverer` 发现:
  - family SOFT: `GSE*_family.soft.gz`
  - Series Matrix: `GSE*_series_matrix.txt.gz`
  - supplementary directory 中的 csv / tsv / txt / xlsx / gz 等文件
- `geo_metadata_profile_service` 会把 manifest 与 family SOFT / Series Matrix metadata 合并，形成 supplementary preview。
- 文件角色预测覆盖:
  - `expression_matrix`
  - `sample_metadata`
  - `platform_annotation`
  - `differential_result_table`
  - `raw_data`
  - `unknown`
- supplementary expression candidate 的关键词包括 count / counts / CPM / FPKM / TPM / normalized / expression / matrix。
- RAW / heavy 文件识别包括 FASTQ / SRA / CEL / BAM / CRAM / RAW tar / tgz / zip 等，默认 risk 较高且不默认选择。

不是只下载 family.soft:

- 第一阶段 `execute_download=True` 的 GEO path 会下载 family SOFT 并写 asset manifest。
- 第二阶段 `download_geo_manifest_assets()` 可基于 manifest 下载 Series Matrix 和 supplementary files。
- 当前 UI 已有“下载补充文件”动作入口，但还不是完整的多文件勾选下载 UI。

限制:

- 当前 manifest discovery 基于 NCBI HTTPS directory listing；没有在本阶段验证 live 网络。
- asset manifest 中有文件名、URL、状态、role、summary，但下载候选 UI 仍偏粗粒度，未充分暴露“用户选择哪些文件下载”的完整体验。
- 文件大小在 directory listing 未必全部填充；已有 size field 和大文件风险逻辑，但远端 size 获取不完整。

## supplementary / RAW / platform 文件处理能力结论

Current:

- supplementary processed table:
  - 当前 recognition 能识别 CSV/TSV/TXT/XLSX 表格中的 expression/count/FPKM/TPM/metadata/annotation/imported DEG 候选。
  - `project_recognition.py` 会区分 imported DEG result 和 expression matrix，不应把 imported DEG 当成重新计算输入。
- RAW:
  - 当前下载候选和 metadata profile 能识别 RAW/heavy 风险并不默认下载。
  - 当前 recognition 对 RAW 只适合 metadata / unsupported / archive 层面的提示，不做 FASTQ/CEL/SRA 预处理。
- platform:
  - 当前 family.soft parser 可发现 platform annotation presence。
  - 当前 Series Matrix parser 输出 platform accession / platform reference hint。
  - 当前 standardization confirmation 将 probe_id / unknown 作为需要平台注释确认的 gene ID 状态。

Legacy:

- `download_validator.py` 对 supplementary 和 RAW 的分类更丰富，有 scoring、organized output、data_asset_index、module1_handoff。
- `model9/geo_readiness/platform_annotation_parser.py` 有 probe -> gene symbol mapping quality report。

结论：supplementary/RAW/platform 的“发现与分类”能力较强；正式 platform mapping 和 RAW preprocessing 不建议进入下一次 Integration Preview。

## 下载 manifest / cache / project handoff 能力结论

已有能力:

- Download queue / request / receipt:
  - `DatasetDownloadService` 写 `acquisition/download_requests/*.json` 和 `acquisition/download_receipts/*.json`。
  - 每个下载任务有 `download_id`、target dir、status、message、downloaded files、asset manifest path。
- cache:
  - family SOFT 和 remote asset downloader 会复用已有非空文件，返回 “Loaded existing ... from project cache”。
- project handoff:
  - 下载成功后调用 `register_acquisition()`，将 `downloaded_files` 作为 referenced paths 登记到项目。
  - acquisition record / handoff 保留 `source_files`，可进入当前待处理数据集与 recognition。
- manifest:
  - GEO asset manifest: `biomedpilot.geo_asset_manifest.v1`
  - TCGA / GTEx download manifest: status `pending_data_file_download`
- B5.10A 兼容:
  - 本地多文件导入已改为文件级显示，但 acquisition source_files 仍按批次保留。
  - GEO manifest 下载后 register 的 downloaded files 可作为 source_files 进入待处理数据集。

缺口:

- 没有持久化的后台下载队列调度器。
- 没有正式取消下载 UI。
- retry 主要靠重新执行或 cache 命中，不是明确 retry policy。
- 进度回调仅在部分 UI 工作流存在，GEO remote asset download 当前是同步循环写文件。
- 用户选择具体 supplementary 文件下载的 UI 尚不完整；默认 `download_geo_manifest_assets()` 下载 selected asset types。

结论：download manifest/cache/project handoff 能力已存在，可 scoped carry-over 到 Integration Preview；后台队列、取消、细粒度重试不建议塞入下一次预览。

## 文件识别能力结论

当前已存在:

- Series Matrix parser:
  - `geo_series_matrix_parser.py` 支持 `.txt` / `.txt.gz`、metadata、sample accession、sample fields、matrix region、dimensions、ID_REF、value type candidate、species evidence。
- family.soft parser:
  - `geo_family_soft_parser.py` 支持 SERIES / PLATFORM / SAMPLE blocks、sample metadata、phenotype candidates、platform table presence、sample expression table presence。
- supplementary processed table parser:
  - `project_recognition.py` 的 tabular / xlsx profile 可识别 expression/count/FPKM/TPM、sample metadata、clinical、annotation、imported DEG。
- clinical/phenotype:
  - tabular profile、group preview、geo metadata profile 能发现候选字段；不会自动确认分组。
- RAW metadata:
  - RAW/heavy 文件主要在 download candidate / validator 层识别，不进入正式预处理。
- species / gene ID / sample metadata / group candidate:
  - Series Matrix 和 SOFT parser 输出 species evidence、gene_id_type candidate、sample metadata、phenotype candidates。

Legacy 可参考:

- `download_validator.py` 的 scoring / strategy / handoff 对文件用途判断更成熟。
- `model9/series_matrix_parser.py`、`model9/soft_parser.py` 是较干净的 parser 设计参考，但当前 B5.8B/B5.9 已在新架构中实现对应能力。

结论：当前文件识别主链路已明显强于早期 container-only 状态。后续重点应是将 GEO file discovery 的 selected assets 更顺滑地送入 recognition，而不是重写 parser。

## 标准化资产能力结论

当前 runtime 已有两层标准化相关能力:

1. 标准化确认:
   - `collect_standardization_candidates()` 从 recognition 输出读取 expression matrix、sample metadata、group candidates、species、gene ID、platform annotation、imported DEG candidates。
   - `save_standardization_confirmation()` 写 `manifests/standardization_confirmation.json`。
   - readiness 分离 `standardization_confirmed`、`deg_preflight_ready`、`imported_result_ready`。

2. 轻量标准化资产注册:
   - `generate_standardized_assets()` 写:
     - `manifests/standardized_assets_registry.json`
     - `standardized_data/analysis_ready_assets/analysis_ready_manifest.json`
     - `manifests/data_processing_task_plan.json`
   - 明确 warning: 当前为资产注册和轻量校验，不等于正式 biological normalization。

已有但未正式实现:

- expression matrix asset registration。
- count / FPKM / TPM / normalized expression 类型确认。
- sample metadata asset。
- phenotype/group candidate and confirmation。
- species confirmation。
- probe_id / unknown gene ID confirmation and platform mapping warning。
- imported DEG candidate 浏览语义。

缺口:

- 不做真实 normalization。
- 不做 ID_REF -> gene symbol/gene ID 正式映射。
- 不做 sample name 对齐的最终 materialized asset。
- `analysis_ready_manifest` 仍是 registry/readiness 层，不等于可直接分析的标准化矩阵。
- ReleaseBuild archive `model9/local_data/standardizer.py` 有复制和 validation report，但 schema 与当前 `standardization_confirmation.json` 不兼容，建议只借鉴验证规则。

结论：当前标准化资产链路是“候选确认 + manifest + registry”，不是完整标准化计算。Integration Preview 可以展示确认与 readiness，但不能承诺完成标准化或真实 DEG。

## 兼容性判断

可 scoped carry-over:

- GEO asset manifest discovery 到 UI 的文件选择体验。
- `geo_metadata_profile_service` 的 supplementary preview、priority、risk、recommendation 文案。
- `DatasetDownloadService` 的 request / receipt / cache / acquisition registration。
- legacy `download_validator.py` 的文件 scoring 规则，作为只读分类参考或 dev audit helper。
- legacy `module1_readers.py` 的 handoff normalization 思路，前提是映射到当前 `acquisition_record` / `recognized_files` / `standardization_confirmation`。
- `model9/platform_annotation_parser.py` 的 mapping quality checks，可在后续平台映射预审中参考。
- `model9/local_data/standardizer.py` 的 validation checks，可在标准化确认后的资产校验阶段参考。

建议重写或保守重构:

- 后台下载队列 / cancel / retry / progress。
- 用户级 supplementary 文件选择 UI。
- standardization materialization 和 sample name 对齐。
- ID_REF -> gene symbol 正式映射。
- RAW preprocessing。

不建议进入下一次 Integration Preview:

- 真实 DEG executor。
- limma / DESeq2 / edgeR。
- RAW FASTQ/SRA/CEL preprocessing。
- 平台探针到 gene symbol 的自动正式映射。
- PubMed 文献检索接入 Bioinformatics 数据获取主线。
- 自动确认分组。
- 把 imported DEG 写成软件重新计算结果。
- 大规模迁移 legacy Module1/Module3 UI 或旧 workflow。

对其他模块影响:

- Scoped carry-over 可限定在 `app/bioinformatics/**` 和 `tests/bioinformatics|tests/ui`。
- 不需要修改 Meta / LabTools / UIShell / MainLine / Integration / ReleaseBuild。
- 不应改变 imported DEG report loop 或 report builder 安全语义。

## 下一次 Integration Preview 的 Bioinformatics 功能边界建议

建议纳入:

- 本地多文件导入，文件级待处理显示。
- GSE 编号检索和中文主题检索的 draft / candidate / user-confirmed online search。
- GEO family SOFT 元数据下载。
- GEO asset manifest: Series Matrix / supplementary / RAW 风险发现。
- 用户选择下载 Series Matrix 和高优先级 processed supplementary candidate。
- 下载后加入待处理数据集并保留完整 `source_files`。
- recognition: Series Matrix、family.soft、XLSX/CSV/TSV processed matrix、metadata、annotation、imported DEG。
- standardization confirmation: 用户确认表达矩阵、value type、species、gene ID、group design。
- readiness: standardization_confirmed / deg_preflight_ready / imported_result_ready。
- 报告草稿只写“候选 / 用户导入 / 当前未运行真实 DEG”。

不建议纳入:

- 真实 DEG、富集、热图、火山图。
- 自动平台映射和自动分组确认。
- RAW 数据下载或预处理。
- PubMed 检索。
- 不可取消的大批量后台下载。

## 推荐下一阶段任务顺序

B5.13 — GSE file discovery and download candidate carry-over

- 将 GEO asset manifest 中的 Series Matrix / supplementary / RAW 风险信息转成用户可选择的下载候选 UI。
- 重点使用 current `HttpsGeoAssetManifestDiscoverer` 和 `GeoMetadataProfileService`，不要迁移旧 UI。

B5.14 — Online download manifest and pending dataset handoff

- 把用户选择的 candidate files 下载到项目数据区。
- 写 request / receipt / asset manifest。
- 注册 acquisition，验证 B5.10A 文件级待处理表格和 recognition `source_files` handoff。

B5.15 — Chinese topic search query draft carry-over

- 收敛中文 query draft、local model 提示、GEO/TCGA/GTEx 分源候选文案。
- 保持 PubMed 排除测试。

B5.16 — Acquisition-to-recognition-to-standardization desktop test

- 手动验证 GSE 检索 -> file candidate -> download -> pending dataset -> recognition -> standardization confirmation。

Integration readiness audit

- 审计 UI 文案、raw path 脱敏、forbidden phrases、readiness 语义、无真实 DEG 误导。

Integration scoped carry-over

- 只合入已通过 desktop manual test 的 Bioinformatics scoped changes。

ReleaseBuild Integration Preview package

- 在 Integration Preview 边界确认后再打包；需单独执行 LaunchServices / Finder-style launch gate。

## 验证

- 本阶段只新增 audit report。
- 未修改 runtime。
- 未联网下载。
- 未修改 MainLine / Integration / ReleaseBuild / Meta / LabTools / UIShell。
- 未删除未跟踪 `docs/bioinformatics/Bioinformatics_handoff_report_20260513.md`。
- 需运行：`git diff --check`。
