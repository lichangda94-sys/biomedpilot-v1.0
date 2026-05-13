# Stage AB13 - Internal Beta Sample Project Pack

## 本阶段目标

准备 Meta Analysis internal beta sample project pack，提供小型治疗效果样例和 biomarker/prevalence/correlation 样例。只提交 source inputs、expected manifests 和 tester walkthrough；不提交生成的报告、图表、缓存或 ZIP 输出。

## Continuity Audit

- 当前分支：`codex/biomedpilot-root`
- 起始 HEAD：`50a6234 feat(meta): harden report template`
- 工作区状态：仅存在既有未跟踪 `test_inputs/`，本阶段未修改或提交该目录。
- 审计正式项目模块：
  - `examples/meta_analysis_e2e_project`
  - `examples/meta_analysis_realistic_project`
  - `docs/meta_sample_project_walkthrough.md`
  - `docs/meta_known_limitations.md`
  - `docs/meta_internal_beta_readiness.md`
  - `tests/meta_analysis/test_stage_v_internal_beta_readiness.py`
  - `tests/meta_analysis/test_stage_z_release_candidate_freeze.py`
- 已有能力：Stage M/W 样例输入、internal beta readiness docs、known limitations。

## Legacy Capability Audit

- 检查 legacy 目录中 sample project / walkthrough / demo project 相关文档。
- legacy 主要是旧 shell demo walkthrough，不读取当前 BioMedPilot manifest / audit / lineage。
- 本阶段未迁移 legacy demo；原因是 AB13 需要当前正式项目 examples、expected manifest 和测试可验证服务。

## 本阶段新增内容

新增 sample pack：

- `examples/meta_analysis_internal_beta_samples/treatment_effect_binary_or`
  - source input: `inputs/literature.csv`
  - expected import count: 3
  - expected duplicate count: 1
  - expected screening status: 2 included
  - expected extraction: binary `Clinical response`, OR, two seeded studies
  - expected analysis: random model testing run, pooled OR direction greater than 1 in seeded data
- `examples/meta_analysis_internal_beta_samples/biomarker_prevalence_correlation`
  - source input: `inputs/literature.csv`
  - expected import count: 3
  - expected duplicate count: 0
  - expected screening status: 3 included
  - expected extraction: proportion and correlation seeded rows
  - expected analysis: logit transformed proportion and Fisher z transform notes

新增 service：

- `InternalBetaSampleProjectService`
  - lists sample manifests;
  - validates input files exist;
  - rejects manifests that reference generated ZIP/report/figure outputs;
  - reports missing sample as clear error.

新增 docs：

- `docs/meta_internal_beta_walkthrough.md`
- Updated `docs/meta_sample_project_walkthrough.md`
- Updated `docs/meta_known_limitations.md`

## Data Center / Task Center / Audit / Manifest / Lineage 影响

- 本阶段只添加 committed sample inputs、expected manifests、docs 和 validation service。
- 不写项目运行 artifacts。
- 不新增 Data Center / Task Center 类型。
- 不修改 audit / lineage 主链。

## 测试

新增：

- `tests/meta_analysis/test_stage_ab13_internal_beta_sample_project_pack.py`

覆盖：

- sample pack 可列出两个样例；
- expected import / duplicate / extraction / analysis metadata 可读取；
- source input files 存在；
- manifest 不引用生成的大型输出；
- missing sample 返回明确 error；
- walkthrough / limitations docs 存在并标记 Developer Preview / testing。

## 当前限制

- 样例 extraction values 是 validation seeds，不是临床精校数据。
- 样例不自动生成正式报告或图表；生成输出应在临时项目目录中完成。
- 不包含正式 PRISMA 2020 图或正式 PDF。
- 不包含自动 PubMed/Web of Science/CNKI/WanFang 检索。

## 下一阶段建议

AB1-AB13 的主要阶段已完成。下一步建议进入一次综合 audit：从 sample pack 开始运行导入、去重、筛选、全文、提取、质量评价、analysis setup、report 和 reproducibility 的 end-to-end beta rehearsal，并记录 UI 阻塞点。
