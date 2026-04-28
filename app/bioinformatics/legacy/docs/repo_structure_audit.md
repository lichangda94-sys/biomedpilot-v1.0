# 仓库结构审计与线路分布

适用范围：`【仓库整理-main结构审计】`

## 1. 审计结论总览

- 当前 main 主线面向 GEO 桌面工作流，用户入口在 `geo_tool/`，业务主链依赖 `geo_pipeline/` 与 `geo_processing/`。
- `geo_processing/` 是明确的 shared layer，承接下载验收、detector、Module 1 合同读取，以及 Module 3 标准资产布局。
- `configs/`、`scripts/`、`tcga_gtex/` 构成 Module 4 规则与资源线；Module 4 当前通过 `geo_tool/main.py` 查询 / 结果分流层提供可选 runtime 路径；`tests/` 与启动包装脚本主要落在 Module 9。
- `ui/module3_sandbox.py`、`ui/module3_sandbox_formatters.py`、`tests/test_module3_sandbox.py`、`tests/test_geo_workflow_integration.py` 属于有 git 历史和导入证据的历史缺件恢复项。

## 2. 顶层目录职责

- `geo_tool/`
  - 桌面 GUI、启动包装脚本、GEO 工作流封装、兼容入口。
- `geo_pipeline/`
  - Module 1 下载与处理的主实现包。
- `geo_processing/`
  - shared validator、detector、Module 1 readers/contracts、Module 3 资产布局。
- `ui/`
  - Module 3 sandbox UI 与仅格式化辅助代码。
- `configs/`
  - shared 标准、规则 JSON、comparison / gene panel 目录。
- `scripts/`
  - smoke 测试驱动、lexicon 构建与覆盖审计脚本。
- `tcga_gtex/`
  - 独立 TCGA/GTEx facade、adapter、search、lexicon、models。
- `tests/`
  - 仓库结构 smoke、Module 1、Module 3、Module 4、facade、literature 回归。
- `docs/`
  - 设计说明与本结构审计文档。

## 3. Canonical entrypoint 与兼容入口

当前 canonical entrypoint：

- `python geo_tool/run_geo_tool.py`

主线共享入口：

- `geo_tool/main.py`
- `geo_tool.geo_workflow.run_download_and_process_workflow`
- `geo_pipeline.download.download_core_geo_records`
- `geo_pipeline.process.process_from_local_family_soft`
- `geo_processing.validate_downloaded_dataset`
- `geo_processing.detect_dataset`
- `geo_processing.load_module1_dataset_context`

## 3.1 主线调用面契约

当前主线正式调用面最小集合固定为：

- `geo_tool/run_geo_tool.py`
- `geo_tool/main.py`
- `geo_tool/geo_workflow.py`
- `geo_pipeline.download.download_core_geo_records`
- `geo_pipeline.process.process_from_local_family_soft`
- `geo_processing.validate_downloaded_dataset`
- `geo_processing.detect_dataset`
- `geo_processing.load_module1_dataset_context`

canonical surface：

- `geo_tool/run_geo_tool.py`
- `geo_tool/main.py`
- `geo_tool/geo_workflow.py`
- `geo_pipeline.download.download_core_geo_records`
- `geo_pipeline.process.process_from_local_family_soft`
- `geo_processing.validate_downloaded_dataset`
- `geo_processing.detect_dataset`
- `geo_processing.load_module1_dataset_context`

wrapper surface：

- `geo_tool/run_geo_tool.sh`
- `geo_tool/run_geo_tool.bat`
- `geo_tool/bootstrap_geo_tool.sh`
- `geo_tool/bootstrap_geo_tool.bat`

legacy surface：

- `download_geo_full_only.py`
- `process_geo_family_soft.py`
- `download_supplement_and_sra.py`

duplicate surface：

- `geo_tool/geo_pipeline/`
- `geo_pipeline.download.download_full_family_soft`

冻结规则：

- canonical surface 可以继续作为当前 GEO 主线扩展面。
- wrapper surface 只允许继续做入口包装，不得承载新的业务编排。
- legacy surface 冻结为兼容面，不重新接回 `geo_tool/main.py` 或 `geo_tool/geo_workflow.py`。
- duplicate surface 仅保留、不扩展，不作为主线新增调用落点。

## 3.2 Module 4 main.py routed optional runtime path 契约

当前 Module 4 状态固定为 `main.py routed optional runtime path`。

冻结结论：

- 接入位置固定为 `geo_tool/main.py` 的查询 / 结果分流阶段。
- `geo_tool/geo_workflow.py` 是禁止接入位置，Module 4 不得挂入当前 GEO 下载/处理编排链。
- `search_tcga_gtex`、`resolve_tcga_gtex_files` 已作为主界面 TCGA/GTEx 可选查询 / 结果分流路径暴露。
- `tcga_gtex/mainline_bridge.py` 是当前可测试 bridge，负责分流摘要、locator 判断和最小 runtime 编排。
- 对具备 `local_path`、`download_url` 或 metadata locator 的记录，可选 runtime 可执行
  `download_tcga_gtex_dataset -> build_tcga_gtex_bundle -> get_tcga_gtex_summary`。
- 缺 locator 时必须明确 failed，不得伪装下载成功。

说明：

- Module 4 当前不是 canonical GEO workflow stage。
- Module 4 当前不是生产级 TCGA/GDC/GTEx 下载器。
- Module 4 失败不得阻断现有 GEO workflow。

## 3.3 阶段性验收基线

当前仓库已经形成“阶段性可用基线”，但不是最终产品发布版。

当前可作为阶段性验收口径的主线描述：

- canonical GEO mainline 固定为
  `geo_tool/run_geo_tool.py -> geo_tool/main.py -> geo_tool/geo_workflow.py`
- Module 1 已作为当前 GEO 下载 / 验收 / 识别 / 处理主体接入主线
- Module 3 当前状态是 `mainline post-workflow action`
- Module 4 当前状态是 `main.py routed optional runtime path`
- Module 9 当前可以代表主线最小可用性

当前不得作为阶段性验收口径的描述：

- 不得把当前仓库描述为最终产品发布版
- 不得把 Module 3 描述为 canonical workflow stage
- 不得把 Module 4 描述为 canonical GEO workflow stage
- 不得把 Module 4 描述为生产级 TCGA/GDC/GTEx 下载器

更完整的阶段性验收基线定义见：

- `docs/mainline_acceptance_baseline.md`

## 4. 模块线路映射

- `【主线】`
  - `geo_tool/run_geo_tool.py`
  - `geo_tool/main.py`
  - `geo_tool/geo_workflow.py`
- `【模块1】`
  - `geo_pipeline/`
  - `geo_processing/download_validator.py`
  - `geo_processing/module1_contracts.py`
  - `geo_processing/module1_readers.py`
  - `geo_processing/detector/`
- `【模块3】`
  - `ui/`
  - `geo_processing/module3_assets.py`
  - `tests/test_module3_sandbox.py`
- `【模块4】`
  - `configs/`
  - `scripts/build_english_core_lexicon.py`
  - `scripts/audit_lexicon_coverage.py`
  - `tcga_gtex/`
  - `tcga_gtex/mainline_bridge.py`
- `【模块9】`
  - `tests/`
  - `geo_tool/bootstrap_geo_tool.sh`
  - `geo_tool/bootstrap_geo_tool.bat`
  - `geo_tool/run_geo_tool.sh`
  - `geo_tool/run_geo_tool.bat`
  - `.github/workflows/module9-smoke.yml`

## 5. Shared 层职责

`geo_processing/` 是当前最关键的 shared 层：

- `download_models.py`
  - Module 1 / detector / sandbox 共用数据模型。
- `download_validator.py`
  - 下载验收、文件检查、报告导出。
- `module1_contracts.py`
  - Module 1 合同与 supporting outputs 生成。
- `module1_readers.py`
  - new schema first / legacy fallback 读取入口。
- `module3_assets.py`
  - Module 3 标准资产布局与动态状态合并。
- `detector/`
  - 数据集识别、规则、模型与路由。

## 6. 本轮发现的结构问题

### 已确认并处理

1. `geo_tool/main.py` 直接导入 `ui.module3_sandbox`，但当前工作树缺 `ui/module3_sandbox.py`
   - 证据：`geo_tool/main.py` 导入；`ui/__pycache__/module3_sandbox*.pyc` 存在；`git log --all --stat` 显示该文件曾在 `dffcd16` 出现。
2. `tests/test_module3_sandbox.py` 与 `tests/test_geo_workflow_integration.py` 在 AGENTS / docs / 历史提交里有明确位置，但当前工作树缺失
   - 证据：`AGENTS.md` 最小测试矩阵、`docs/task1_task2_asset_contract_and_refactor_plan.md`、`git log --all --stat`。
3. `README.md` 仍以“3 个独立部分”叙述仓库，未覆盖 `geo_processing/`、`ui/`、`configs/`、`tcga_gtex/` 等当前结构
   - 证据：README 当前内容与 `AGENTS.md` repo snapshot 不一致。

### 已确认但仅记录

1. 大量正式源码、测试、配置仍处于未跟踪状态
   - 证据：`git status --short`
   - 说明：本轮做结构整理与恢复，但不替用户做版本控制决策。
2. `agent.md`、`agent_local.md`、`geo_tool/未命名.txt` 无导入链，但含人工规则/词表内容
   - 说明：列入人工确认，不直接删除。

## 7. 历史缺件恢复说明

本轮按历史提交恢复的文件：

- `ui/module3_sandbox.py`
- `ui/module3_sandbox_formatters.py`
- `tests/test_module3_sandbox.py`
- `tests/test_geo_workflow_integration.py`

恢复依据：

- `git log --all --stat`
- `git show dffcd16398434c00f2f565901bcca470a45999f4`
- `git show 73d0947adaff39649fd394d0357a5c6d6f1292e0`
- 当前导入链与 AGENTS 最小测试矩阵

这些恢复项属于结构补齐，不计为当前模块新功能开发。

## 8. 清理策略

可直接清理：

- `.DS_Store`
- `.Rhistory`
- `__pycache__/`
- `geo_downloads/`
- `literature_output/`
- `tmp_diagnostics_*/`
- `geo_tool/workflow_test_output/`
- 不被当前脚本使用的嵌套虚拟环境 `geo_tool/.venv/`

谨慎处理：

- repo 根与 `geo_tool/` 下的 `GSE*.txt`
- `agent.md`
- `agent_local.md`
- `geo_tool/未命名.txt`

这些文件需要先区分“调试输入 / 快速缓存 / 备用资料 / 手工草稿”，不在本轮直接删源码或文档。

## 9. 最小复现路径

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r geo_tool/requirements.txt
python geo_tool/run_geo_tool.py --check
python scripts/run_smoke_tests.py
python geo_tool/run_geo_tool.py
```

## 10. 任务线路命名规范

后续新任务应在提示词开头显式标线路，例如：

- `【主线】`
- `【模块1】`
- `【模块3】`
- `【模块4】`
- `【模块9】`
- `【仓库整理】`
- `【新线路：xxx】`

如果发现需要拆出去的问题，只登记为“建议新线路”，不要在当前线路混做。
