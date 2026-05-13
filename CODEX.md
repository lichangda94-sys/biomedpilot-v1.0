# CODEX.md - AI Gateway

## 当前工作区

路径：/Users/changdali/Developer/biomedpilot v1.0/AI  
分支：dev/ai-gateway  

## 职责

本工作区负责 AI Gateway、本地模型接入、模块策略、隐私策略和审计。

## 核心规则

- AI 默认关闭。
- 本地模型必须通过 AIGateway.generate()。
- 不得直接调用 Ollama HTTP。
- 不保存 raw prompt / raw response。
- 只保存必要审计摘要。
- AI 只生成草稿或建议。
- 用户确认后才允许进入检索、筛选、提取或报告流程。
- AI 不得自动执行下载、分析或最终结论生成。

## 测试
