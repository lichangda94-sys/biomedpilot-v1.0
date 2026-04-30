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

## Meta 文献导入与文献库中文页面

在 `Meta 分析模块` 左侧导航中：

1. 打开 `文献导入 Literature Import`。
2. 选择或粘贴 RIS / NBIB / CSV 文件路径。
3. 填写来源数据库、检索日期、检索式说明和去重模式。
4. 点击导入后查看中文导入诊断摘要、warning 列表和失败记录预览。
5. 下一步进入 `文献库 Literature Library` 或 `去重审核 Duplicate Review`。

在 `文献库 Literature Library` 中：

- 红色表示高重复风险。
- 黄色表示可能重复或标识符冲突。
- 灰色表示疑似重复。
- 绿色只表示“未发现明显重复风险”，不代表文献质量高或可信。

当前文献库仍是只读 testing 页面，不会自动删除、合并或排除文献。
