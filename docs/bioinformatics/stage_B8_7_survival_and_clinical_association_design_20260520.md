# B8.7 Survival and Clinical Association Design / Preflight

## 旧实现审计与迁入判断

| 范围 | 判断 | 可复用内容 | 不直接迁入原因 | 本阶段处理 | 测试 |
| --- | --- | --- | --- | --- | --- |
| `services/survival_service.py` / TCGA clinical code | 最小迁入 | OS_time/OS_event、patient/sample mapping 思路 | 旧 preview 不是 formal KM/Cox/log-rank | 新 `clinical_analysis/*` 只做 preflight | survival tests |
| `project_readiness.py` / `analysis_inputs/*` / `results/*` | 直接保留 | readiness 与 input package boundaries | 正式 survival 仍需新 package schema | 新 survival package 消费 B8.1 clinical package | preflight tests |
| `config/survival_defaults.yaml` | 不迁入，仅记录 | 默认字段名参考 | 默认策略不能自动执行 formal stats | 只保留 time/event 参数 | 文档记录 |
| old KM/Cox preview cards | 不迁入，仅记录 | UI 文案和字段提示 | preview 不等于 formal result | KM/Cox/log-rank 按钮应禁用 | UI boundary |
| lifelines / R survival/survminer | 不迁入 | optional backend idea | 未声明依赖，打包风险 | 只检测，不调用 | dependency tests |

## Survival Package Schema

新增 `clinical_analysis/*`。字段包括 survival package id、input package id、clinical/expression assets、sample-case mapping、time/event fields、unit、event coding、censoring policy、grouping policy、missingness、event/sample counts、blockers/warnings。

## Survival Preflight

检查 OS_time、OS_event、event coding、censoring、sample-case mapping、event count、表达分组策略、missingness、backend dependency。`lifelines` 缺失时显示 blocker，不 traceback。

## Clinical Association Preflight

识别 continuous、categorical、binary、ordinal/time-to-event、unknown variables，输出 missingness、allowed test candidates 和多因素模型风险提示。当前不执行正式统计。

## 后端决策

建议保持 preflight/detection-only，待依赖架构成熟后再选择 Python lifelines 或 R survival/survminer。

## UI 变化

Survival/clinical 页面应显示“仅预检查”；KM/Cox/log-rank 和 HR formal result 禁用；不得显示 clinical advice。

## 未实现边界

未运行 KM/Cox/log-rank，未生成 KM plot，未生成 Cox HR formal result，未自动 median split，未忽略 event/missingness 阈值，未输出临床建议。

## 后续建议

下一阶段先接 UI preflight diagnostics 和后端 dependency settings，再决定是否启用 formal survival statistics。
