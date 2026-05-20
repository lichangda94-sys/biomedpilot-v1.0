# B8.5 Plot Artifact Schema and Basic Plots

## 旧实现审计与迁入判断

| 范围 | 判断 | 可复用内容 | 不直接迁入原因 | 本阶段处理 | 测试 |
| --- | --- | --- | --- | --- | --- |
| `config/plotting_defaults.yaml` | 不迁入，仅记录 | plotting defaults 可供后续样式参考 | 本阶段不渲染图片 | 只生成 plot spec | plot schema tests |
| `results/project_results.py` | 直接保留 | result index 路径 | plot 必须挂到 result entry | registry 更新 `plot_artifacts` | inheritance tests |
| `reports/project_report_builder.py` | 最小迁入 | 报告草稿读取结果 | report-ready 前必须引用 plot artifact | B8.6 gate 检查 plot registration | report tests |
| old volcano-shaped table / preview card | 不迁入，仅记录 | volcano 字段命名参考 | 旧表缺 FDR/semantics 可能误导 formal | 只实现 spec，不消费旧表 | schema tests |
| matplotlib / R plotting | 不迁入 | 无 | 新依赖有打包风险 | 不新增绘图依赖 | dependency snapshot 标记 spec-only |

## Plot Schema

新增 `plots/*`，字段包括 `plot_id`、`plot_type`、source result id/semantics、input package、task run、parameters、plot spec、image/table artifacts、engine/version、dependency snapshot、warnings/blockers。

## 支持 Plot Types

当前支持 spec：`volcano_plot`、`deg_heatmap`、`ora_barplot`、`ora_dotplot`、`correlation_scatter`。`km_plot` 仅保留 schema，默认 blocker。

## 语义继承

testing/exploratory/imported 均继承 warning；preflight-only 不能生成 formal plot；formal result 仍需 validation pass 后才能 downstream。

## UI 变化

结果页面后续应只对可绘图 result 显示 action，不可绘图显示 blocker。当前模块已提供 `create_plot_artifact` 供 UI 接入。

## 未实现边界

未从 raw expression 直接画 volcano，未从 DEG preflight 画 volcano，未从 survival preflight 画 KM，未自动安装 matplotlib/R。

## B8.6 建议

Report-ready gate 应要求所有纳入 figures 的图均有 plot artifact entry。
