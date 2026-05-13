# CODEX.md - ReleaseBuild

## 当前工作区

路径：/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild
分支：dev/release-internal-test

## 职责

本工作区只负责从已验证 MainLine 或已验证发布源同步内部测试打包候选、预打包验证、打包 smoke、包内 metadata 检查和发布前检查。

ReleaseBuild 不做功能开发，不直接吸收未经 Integration 或 MainLine 验证的单一模块分支工作，不把预检或测试级输出描述为正式结果。

## 当前第一任务

执行 ReleaseBuild sync from MainLine pre-package validation：从 MainLine 确认源同步、验证、记录报告，不执行正式打包。

## 禁止事项

- 不要在 ReleaseBuild 做功能开发。
- 不要修改其他 worktree。
- 不要执行正式打包，除非任务明确授权。
- 不要覆盖 `dist/BioMedPilot.app` 或桌面入口。
- 不要推送远程。
- 不要生成假 DEG。
- 不要把 PubMed 放进 Bioinformatics 数据检索。
- 不要把 GEO / TCGA / GTEx 表达分析放进 Meta。
- 不要绕过 AI Gateway。
- 不要保存 raw prompt / response。
- 不要在主 UI 暴露 manifest、schema、branch、raw path。

## 测试

按任务范围运行：

- `git diff --check`
- `QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/meta_analysis -q`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/shared -q`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q`
- `python3 scripts/run_tests.py`

正式打包命令和桌面入口刷新需要单独确认。
