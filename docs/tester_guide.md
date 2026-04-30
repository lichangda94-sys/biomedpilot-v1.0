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

## Meta 去重、标准与标题摘要筛选中文页面

完成文献导入后，按顺序检查：

1. 打开 `去重审核 Duplicate Review`，查看重复候选组、匹配原因、canonical candidate 和字段冲突。
2. 只有在看到 merge preview 后，才记录 merge 决策；不要批量自动合并。
3. 打开 `纳入与排除标准 Criteria`，确认纳入标准、排除标准和 readiness status。
4. 打开 `标题摘要筛选 Screening`，逐篇查看题名、摘要、作者、期刊、年份、DOI / PMID 链接。
5. 使用 `纳入`、`排除`、`可能纳入`、`需要复核` 或 `待筛选` 标签记录测试问题。

测试时请特别记录：

- 去重字段冲突是否能用中文理解。
- 排除标准是否能帮助 reviewer 决策。
- `needs_review` 是否清楚表示“需要复核”，不是正式排除。
- 排除记录是否填写了人能看懂的排除原因。

当前这些页面仍为 Developer Preview / testing，不会自动删除文献、自动排除文献或自动完成 reviewer 判断。
