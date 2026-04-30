# BioMedPilot Tester Guide

Status: Developer Preview / testing.

The current maintained tester guide is:

```text
docs/user_testing/tester_guide.md
```

For the internal beta desktop entry, use:

```text
/Users/changdali/Desktop/BioMedPilot.app
```

Before testing, confirm the app version from the Dashboard header or smoke test:

```bash
/Users/changdali/Desktop/BioMedPilot.app/Contents/MacOS/BioMedPilot --smoke-test
```

Expected version identity:

```text
0.1.0-internal-beta · Developer Preview / testing
```

This is not production clinical, statistical, or publication software.

## Meta 中文流程总控

进入桌面入口后：

1. 在 Dashboard 点击 `Meta 分析 Meta Analysis` 或 `新建 Meta 项目`。
2. 进入 `Meta 分析模块`。
3. 左侧第一项是 `流程总控 Workflow Dashboard`。
4. 该页面用中文显示 15 个 Meta 分析步骤、当前状态、下一步建议和需要复核的问题数量。
5. 页面顶部应显示：

```text
0.1.0-internal-beta · 内部测试版 / Developer Preview / testing
```

如果某一步显示“需要复核”，请记录页面、步骤名称、warning 数量和你预期的下一步。
