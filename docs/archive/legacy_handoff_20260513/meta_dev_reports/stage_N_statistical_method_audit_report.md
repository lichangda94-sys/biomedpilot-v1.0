# Stage N Statistical Method Audit Report

## 本阶段目标

复核当前 Meta Analysis 统计核心不是“能跑即可”，而是在核心效应量、log scale、SE、权重、异质性和高级基础指标上有明确 reference fixture 与容差测试。

## 实际完成内容

- 新增 `tests/fixtures/meta_stats/reference_cases.json`，记录手工公式参考值和来源说明。
- 新增 `tests/meta_analysis/test_stage_n_statistical_method_audit.py`，覆盖核心统计方法与边界 warning。
- 本阶段未调用 R、外部网络或外部 API。

## Reference 覆盖范围

- OR
- RR
- RD
- MD
- SMD
- HR generic inverse variance
- CI 转 SE
- fixed effect inverse variance pooling
- DerSimonian-Laird random effects pooling
- Q
- I²
- tau²
- zero-event correction
- prevalence logit transformation
- Fisher z correlation transform/back-transform
- diagnostic sensitivity / specificity / PLR / NLR / DOR
- Egger test basic regression

## Reference 来源

Reference 值来自标准公式手工计算并写入 fixture。fixture 明确注明未使用联网、R 包或外部 API。当前 tolerance 使用 `1e-12` 到 `1e-9` 量级，用于检测公式回归；没有通过放宽 tolerance 掩盖差异。

## Edge-case warning 策略

- 零事件 OR/RR 触发 `zero_event_correction_applied`。
- 小样本发表偏倚测试保留用户可读 warning：`Publication bias tests are unreliable when the number of studies is small.`
- 缺失 SE 的 generic inverse variance 可从 CI 推导 SE。

## 未解决统计风险

- 当前 DerSimonian-Laird 只覆盖基础随机效应模型，未覆盖 Hartung-Knapp、REML 或 profile likelihood。
- Diagnostic 只覆盖基础 2x2 指标和 DOR，不是 bivariate/HSROC 模型。
- Egger test 为基础 testing regression；小样本结果不可用于正式结论。
- Network meta-analysis 仍为 not implemented placeholder。

## 测试结果

Stage N 新增 reference tests 覆盖核心效应量、pooling、异质性、转化公式和基础高级指标。

- Stage N focused tests: `7 passed`
- M-P focused tests: `18 passed`
- Full venv pytest: `256 passed`
- Unified `scripts/run_tests.py`: `256 passed`
- Smoke test: passed
- Local shell `python` / `pytest`: unavailable in this environment; venv commands passed.

## 当前状态

Meta Analysis 统计核心仍为 testing。Stage N 增加了公式复核保障，但不代表生产级统计软件认证。
