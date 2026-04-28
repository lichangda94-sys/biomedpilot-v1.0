# 主线阶段性验收基线

适用范围：`【主线】阶段性发布/验收基线固化`

## 1. 基线性质

当前仓库已经形成可重复使用的“阶段性可用基线”。

这份基线：

- 用于当前 GEO 主线的阶段性验收与对内/对外口径统一；
- 用于后续 smoke / regression / 文档说明复用；
- 不是最终产品发布版说明；
- 不代表全部模块都已完成。

## 2. 当前可以宣称的能力边界

- canonical mainline 已基本稳定：
  - `geo_tool/run_geo_tool.py`
  - `geo_tool/main.py`
  - `geo_tool/geo_workflow.py`
- Module 1 已接入主线，是当前 GEO 下载 / 验收 / 识别 / 处理主体。
- Module 3 已进入主线后置动作层：
  - workflow 完成后的结果摘要里可直接看到 Module 3 handoff / standard assets；
  - workflow 完成后可以从当前 GSE 直接进入 Module 3 工作台。
- Module 4 当前状态是 `main.py routed optional runtime path`：
  - 主界面可以进入 TCGA/GTEx search / resolve 可选查询分流；
  - 对具备 `local_path`、`download_url` 或 metadata locator 的记录，可以运行最小
    `download -> bundle -> summary` runtime；
  - 缺 locator 时必须明确 failed，不得伪装成功。
- Module 9 已能代表主线最小可用性。
- shared layer 已稳定支撑 Module 1 主链和 Module 3 handoff / standard assets。

## 3. 当前不能宣称的能力边界

- 不能把当前仓库描述为最终产品发布版。
- 不能把当前仓库描述为全部模块均已完成的完整平台。
- 不能把 Module 3 描述为 canonical workflow stage。
- 不能把 Module 4 描述为 canonical GEO workflow stage。
- 不能把 Module 4 描述为 `geo_tool/geo_workflow.py` stage。
- 不能把 Module 4 描述为生产级 TCGA/GDC/GTEx 下载器。

## 4. 模块正式表述

- Module 1：
  - 已接入主线；
  - 当前是 GEO 下载 / 验收 / 识别 / 处理主体。

- Module 3：
  - 当前状态是 `mainline post-workflow action`；
  - 已完成主线结果可见和 workflow 后动作入口；
  - 尚未成为 canonical workflow stage。

- Module 4：
  - 当前状态是 `main.py routed optional runtime path`；
  - 接入点固定为 `geo_tool/main.py` 的查询 / 结果分流阶段；
  - 禁止接入 `geo_tool/geo_workflow.py`；
  - 当前 runtime 是最小 local/mockable 能力，不是生产级 TCGA/GDC/GTEx 下载器。

- Module 9：
  - 当前状态是“主线最小可用性门禁已到位”；
  - 它代表当前 GEO 主线的最小 smoke / integration 基线。

## 5. 验收最小矩阵

当前阶段性验收基线至少应满足：

```bash
python3 -m unittest tests.test_repo_smoke
python3 scripts/run_smoke_tests.py
python3 -m unittest tests.test_module3_sandbox
python3 -m unittest tests.test_module4_mainline_bridge
python3 -m unittest tests.test_geo_workflow_integration
python3 -m unittest tests.test_tcga_gtex_facade
```

说明：

- `tests.test_repo_smoke` 用于冻结主线口径、调用面契约和 Module 4 main.py 可选分流契约。
- `scripts/run_smoke_tests.py` 用于当前 GEO mainline 的最小可用性门禁。
- `tests.test_module3_sandbox` 用于验证 Module 3 当前 `mainline post-workflow action` 层仍可用。
- `tests.test_module4_mainline_bridge` 用于验证 Module 4 main.py routed optional runtime path 的可测试 bridge。
- `tests.test_geo_workflow_integration` 用于验证 canonical GEO workflow 仍可跑通。
- `tests.test_tcga_gtex_facade` 用于验证 Module 4 facade 的 search / resolve / 最小 runtime 行为稳定。

## 6. 版本控制锚点

当前阶段性基线对应的提交范围：

- `57cb306^..74553a7`

该范围包含以下阶段性基线提交：

- `57cb306 chore: restore mainline support files`
- `01bedc0 docs: freeze staged mainline acceptance baseline`
- `24234d9 test: strengthen mainline smoke gate`
- `a822609 feat(module3): expose post-workflow action path`
- `fbfa838 feat(module4): add minimal tcga-gtex runtime`
- `74553a7 feat(module4): route optional runtime through main window`

建议 tag：

- `v0.1-mainline-baseline`

建议 tag 指向：

- `74553a7 feat(module4): route optional runtime through main window`

创建 tag 前应确认：

- `git status --short` 无输出；
- 本文档第 5 节验收最小矩阵已通过；
- 当前状态仍未把 Module 3 描述为 canonical workflow stage；
- 当前状态仍未把 Module 4 描述为 `geo_tool/geo_workflow.py` stage 或生产级 TCGA/GDC/GTEx 下载器。
