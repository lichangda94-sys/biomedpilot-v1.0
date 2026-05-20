# CODEX.md - Integration

## 当前工作区

路径：/Users/changdali/Developer/biomedpilot v1.0/Integration
分支：dev/integration

## 职责

本工作区只做阶段性合并、冲突解决、全量测试和内部测试版准备。

## 集成板块规则

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

## 测试
