# CODEX.md - Integration

## 当前工作区

路径：/Users/changdali/Developer/biomedpilot v1.0/Integration
分支：dev/integration

## 职责

本工作区只做阶段性合并、冲突解决、全量测试和内部测试版准备。

ReleaseBuild 相关内容只能作为已验证打包候选和预发布检查输入纳入；Integration 不直接发布、不推送远程。

## 集成板块规则

- Bioinformatics Analysis 负责生信分析模块主流程：项目首页 -> 数据选择 -> 数据识别 -> 数据标准化 -> 分析任务中心 -> 结果浏览 -> 项目报告。
- Meta Analysis 当前是 Developer Preview / testing；统计、报告、handoff 和 AI/OCR 输出都必须保留 draft / testing-level / human-review wording。
- LabTools 在 Integration 中同时保留桌面 UI 入口和顶层 `labtools` 公共后端包。
- AI Gateway 负责本地模型接入、模块策略、隐私策略和审计。
- AI 默认关闭。
- 本地模型必须通过 `AIGateway.generate()`。
- 不得直接调用 Ollama HTTP。
- 不保存 raw prompt / raw response。
- 只保存必要审计摘要。
- AI 只生成草稿或建议。
- 用户确认后才允许进入检索、筛选、提取或报告流程。
- AI 不得自动执行下载、分析或最终结论生成。

## 禁止事项

- 不要在 Integration 直接开发大功能。
- 不要不记录冲突处理。
- 不要把 dry-run 或 testing 结果写成 production。
- 不要在测试失败时打包成内部测试版。
- 不要执行 PubMed 文献检索作为生信数据结果。
- 不要把 Meta 文献候选混入生信。
- 不要生成假 DEG、假火山图、假富集结果。
- 不要让 AI 直接执行下载或分析。
- 不要在主 UI 暴露大量 manifest、schema、branch、asset id、raw path。
- 不要让 Meta active services 重新依赖 `app/meta_analysis/legacy/**`。
- 不要覆盖 `dist/BioMedPilot.app` 或桌面入口，除非任务明确授权。
- 不要推送远程。

## 测试

按任务范围运行：

- `git diff --check`
- `QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/meta_analysis -q`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/shared -q`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q`
- `python3 scripts/run_tests.py`
